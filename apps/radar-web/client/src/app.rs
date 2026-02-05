//! Application state and main loop.

use crate::protocol::RadarFrame;
use crate::renderer::Renderer;
use crate::websocket::FrameClient;
use std::cell::RefCell;
use std::rc::Rc;
use wasm_bindgen::prelude::*;
use web_sys::HtmlCanvasElement;

/// Application state.
pub struct App {
    renderer: Renderer,
    client: FrameClient,
    frame_count: u64,
    last_fps_update: f64,
    fps: f64,
}

impl App {
    /// Create a new application.
    pub async fn new(canvas: HtmlCanvasElement) -> Result<Self, String> {
        // Build WebSocket URL from current location
        let ws_url = get_websocket_url()?;

        // Create WebSocket client
        let client = FrameClient::new(&ws_url)
            .map_err(|e| format!("Failed to connect WebSocket: {:?}", e))?;

        // Create renderer
        let renderer = Renderer::new(canvas).await?;

        Ok(Self {
            renderer,
            client,
            frame_count: 0,
            last_fps_update: 0.0,
            fps: 0.0,
        })
    }

    /// Process available frames and render.
    pub fn update(&mut self, timestamp: f64) {
        // Process all available frames
        let mut frame_received = false;
        while let Some(frame) = self.client.try_recv() {
            self.process_frame(frame);
            frame_received = true;
        }

        // Update FPS counter
        if frame_received {
            self.frame_count += 1;
        }

        let elapsed = timestamp - self.last_fps_update;
        if elapsed >= 1000.0 {
            self.fps = (self.frame_count as f64 * 1000.0) / elapsed;
            self.frame_count = 0;
            self.last_fps_update = timestamp;

            // Update FPS display
            if let Some(window) = web_sys::window() {
                if let Some(document) = window.document() {
                    if let Some(counter) = document.get_element_by_id("fps-counter") {
                        counter.set_text_content(Some(&format!("{:.0} FPS", self.fps)));
                    }
                }
            }
        }

        // Render
        self.renderer.render();
    }

    /// Process a received frame.
    fn process_frame(&mut self, frame: RadarFrame) {
        let (n_doppler, n_range) = frame.dimensions();
        log::debug!("Frame: {}x{}, {} bytes", n_doppler, n_range, frame.payload.len());

        // Update renderer with new frame data
        self.renderer.update_texture(&frame.payload, n_doppler, n_range);
    }
}

/// Run the application main loop.
pub async fn run() -> Result<(), String> {
    // Get canvas element
    let window = web_sys::window().ok_or("No window")?;
    let document = window.document().ok_or("No document")?;
    let canvas = document
        .get_element_by_id("radar-canvas")
        .ok_or("No canvas element")?
        .dyn_into::<HtmlCanvasElement>()
        .map_err(|_| "Element is not a canvas")?;

    // Set canvas size to fill container
    let container = canvas.parent_element().ok_or("Canvas has no parent")?;
    let rect = container.get_bounding_client_rect();
    canvas.set_width(rect.width() as u32);
    canvas.set_height(rect.height() as u32);

    log::info!(
        "Canvas size: {}x{}",
        canvas.width(),
        canvas.height()
    );

    // Create application
    let app = App::new(canvas).await?;
    let app = Rc::new(RefCell::new(app));

    // Start animation loop
    start_animation_loop(app);

    Ok(())
}

/// Start the requestAnimationFrame loop.
fn start_animation_loop(app: Rc<RefCell<App>>) {
    let f: Rc<RefCell<Option<Closure<dyn FnMut(f64)>>>> = Rc::new(RefCell::new(None));
    let g = f.clone();

    let app_clone = app.clone();
    *g.borrow_mut() = Some(Closure::wrap(Box::new(move |timestamp: f64| {
        app_clone.borrow_mut().update(timestamp);

        // Request next frame
        if let Some(window) = web_sys::window() {
            let _ = window.request_animation_frame(
                f.borrow().as_ref().unwrap().as_ref().unchecked_ref(),
            );
        }
    }) as Box<dyn FnMut(f64)>));

    // Start the loop
    if let Some(window) = web_sys::window() {
        let _ = window.request_animation_frame(
            g.borrow().as_ref().unwrap().as_ref().unchecked_ref(),
        );
    }
}

/// Build WebSocket URL from current location.
fn get_websocket_url() -> Result<String, String> {
    let window = web_sys::window().ok_or("No window")?;
    let location = window.location();

    let protocol = location.protocol().map_err(|_| "No protocol")?;
    let ws_protocol = if protocol == "https:" { "wss:" } else { "ws:" };

    let host = location.host().map_err(|_| "No host")?;

    Ok(format!("{}//{}/ws/frames", ws_protocol, host))
}
