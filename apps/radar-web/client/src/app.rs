//! Application state and main loop.

use crate::protocol::RadarFrame;
use crate::renderer::{Colormap, Renderer};
use crate::websocket::FrameClient;
use std::cell::RefCell;
use std::rc::Rc;
use wasm_bindgen::prelude::*;
use wasm_bindgen::JsCast;
use web_sys::{HtmlCanvasElement, KeyboardEvent, MouseEvent, WheelEvent};

/// Application state.
pub struct App {
    renderer: Renderer,
    client: FrameClient,
    canvas: HtmlCanvasElement,
    frame_count: u64,
    last_fps_update: f64,
    fps: f64,
    // Local display state
    colormap: Colormap,
    paused: bool,
    debug_overlay: bool,
    // Mouse drag state
    dragging: bool,
    last_mouse_x: f32,
    last_mouse_y: f32,
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
        let renderer = Renderer::new(canvas.clone()).await?;

        Ok(Self {
            renderer,
            client,
            canvas,
            frame_count: 0,
            last_fps_update: 0.0,
            fps: 0.0,
            colormap: Colormap::Inferno,
            paused: false,
            debug_overlay: false,
            dragging: false,
            last_mouse_x: 0.0,
            last_mouse_y: 0.0,
        })
    }

    /// Process available frames and render.
    pub fn update(&mut self, timestamp: f64) {
        // Process state updates from server
        while let Some(state) = self.client.try_recv_state() {
            self.handle_state_update(&state);
        }

        // Process all available frames (unless paused)
        if !self.paused {
            let mut frame_received = false;
            while let Some(frame) = self.client.try_recv_frame() {
                self.process_frame(frame);
                frame_received = true;
            }

            // Update FPS counter
            if frame_received {
                self.frame_count += 1;
            }
        }

        let elapsed = timestamp - self.last_fps_update;
        if elapsed >= 1000.0 {
            self.fps = (self.frame_count as f64 * 1000.0) / elapsed;
            self.frame_count = 0;
            self.last_fps_update = timestamp;
            self.update_fps_display();
        }

        // Render
        self.renderer.render();
    }

    /// Handle state update from server.
    fn handle_state_update(&self, json: &str) {
        // Update HUD elements based on server state
        if let Some(window) = web_sys::window() {
            if let Some(document) = window.document() {
                // Try to parse as state_update
                if json.contains("\"event\":\"state_update\"") {
                    // Extract fields with simple string matching (avoid serde in WASM)
                    if let Some(mode) = extract_json_string(json, "mode") {
                        if let Some(el) = document.get_element_by_id("mode-display") {
                            let text = mode.to_uppercase();
                            el.set_text_content(Some(&text));
                            // Add/remove class for styling
                            if mode == "synthetic" {
                                let _ = el.class_list().add_1("synthetic");
                            } else {
                                let _ = el.class_list().remove_1("synthetic");
                            }
                        }
                    }
                    if let Some(pattern) = extract_json_string(json, "pattern") {
                        if let Some(el) = document.get_element_by_id("pattern-display") {
                            el.set_text_content(Some(&pattern));
                        }
                    }
                    if let Some(mti) = extract_json_bool(json, "mti_enabled") {
                        if let Some(el) = document.get_element_by_id("mti-display") {
                            el.set_text_content(Some(if mti { "ON" } else { "OFF" }));
                            if mti {
                                let _ = el.class_list().add_1("enabled");
                            } else {
                                let _ = el.class_list().remove_1("enabled");
                            }
                        }
                    }
                    if let Some(paused) = extract_json_bool(json, "paused") {
                        if let Some(el) = document.get_element_by_id("paused-display") {
                            el.set_text_content(Some(if paused { "PAUSED" } else { "" }));
                        }
                    }
                }
                // Handle toast messages
                else if json.contains("\"event\":\"toast\"") {
                    if let Some(message) = extract_json_string(json, "message") {
                        show_toast(&message);
                    }
                }
                // Handle export result
                else if json.contains("\"event\":\"export_result\"") {
                    if let Some(path) = extract_json_string(json, "path") {
                        show_toast(&format!("Exported: {}", path));
                    } else if let Some(error) = extract_json_string(json, "error") {
                        show_toast(&format!("Export failed: {}", error));
                    }
                }
            }
        }
    }

    /// Update FPS display.
    fn update_fps_display(&self) {
        if let Some(window) = web_sys::window() {
            if let Some(document) = window.document() {
                if let Some(counter) = document.get_element_by_id("fps-counter") {
                    counter.set_text_content(Some(&format!("{:.0} FPS", self.fps)));
                }
            }
        }
    }

    /// Process a received frame.
    fn process_frame(&mut self, frame: RadarFrame) {
        let (n_doppler, n_range) = frame.dimensions();
        log::debug!("Frame: {}x{}, {} bytes", n_doppler, n_range, frame.payload.len());

        // Update dimension display
        if let Some(window) = web_sys::window() {
            if let Some(document) = window.document() {
                if let Some(el) = document.get_element_by_id("dims-display") {
                    el.set_text_content(Some(&format!("{}×{}", n_doppler, n_range)));
                }
            }
        }

        // Update renderer with new frame data
        self.renderer.update_texture(&frame.payload, n_doppler, n_range);
    }

    /// Handle keyboard input.
    pub fn handle_key(&mut self, key: &str) {
        match key.to_uppercase().as_str() {
            "T" => {
                // Cycle test pattern (server-side)
                self.client.send_command(r#"{"cmd":"cycle_pattern"}"#);
            }
            "M" => {
                // Toggle MTI (server-side)
                self.client.send_command(r#"{"cmd":"toggle_mti"}"#);
            }
            "E" => {
                // Export frame (server-side)
                self.client.send_command(r#"{"cmd":"export"}"#);
            }
            "C" => {
                // Cycle colormap (client-side)
                self.colormap = self.colormap.next();
                self.renderer.set_colormap(self.colormap);
                update_colormap_display(self.colormap.name());
                show_toast(&format!("Colormap: {}", self.colormap.name()));
            }
            "+" | "=" => {
                // Increase gain (client-side)
                self.renderer.adjust_gain(0.1);
                update_gain_display(self.renderer.gain());
            }
            "-" | "_" => {
                // Decrease gain (client-side)
                self.renderer.adjust_gain(-0.1);
                update_gain_display(self.renderer.gain());
            }
            "P" => {
                // Toggle pause (both client-side and notify server)
                self.paused = !self.paused;
                if self.paused {
                    self.client.send_command(r#"{"cmd":"pause"}"#);
                } else {
                    self.client.send_command(r#"{"cmd":"resume"}"#);
                }
            }
            "R" => {
                // Reset to defaults
                self.renderer.reset_view();
                self.colormap = Colormap::Inferno;
                self.renderer.set_colormap(self.colormap);
                self.paused = false;
                self.client.send_command(r#"{"cmd":"reset"}"#);
                update_colormap_display(self.colormap.name());
                update_gain_display(1.0);
                update_zoom_display(1.0);
            }
            "D" => {
                // Toggle debug overlay (client-side)
                self.debug_overlay = !self.debug_overlay;
                toggle_debug_overlay(self.debug_overlay);
            }
            _ => {}
        }
    }

    /// Handle mouse wheel (zoom).
    pub fn handle_wheel(&mut self, delta_y: f64) {
        let factor = if delta_y < 0.0 { 1.1 } else { 0.9 };
        self.renderer.adjust_zoom(factor);
        update_zoom_display(self.renderer.zoom());
    }

    /// Handle mouse down (start drag).
    pub fn handle_mouse_down(&mut self, x: f32, y: f32) {
        self.dragging = true;
        self.last_mouse_x = x;
        self.last_mouse_y = y;
    }

    /// Handle mouse move (drag for pan).
    pub fn handle_mouse_move(&mut self, x: f32, y: f32) {
        if self.dragging {
            let dx = (x - self.last_mouse_x) / self.canvas.width() as f32;
            let dy = (y - self.last_mouse_y) / self.canvas.height() as f32;
            self.renderer.adjust_pan(-dx / self.renderer.zoom(), dy / self.renderer.zoom());
            self.last_mouse_x = x;
            self.last_mouse_y = y;
        }
    }

    /// Handle mouse up (end drag).
    pub fn handle_mouse_up(&mut self) {
        self.dragging = false;
    }

    /// Handle canvas resize.
    pub fn handle_resize(&mut self, width: u32, height: u32) {
        self.canvas.set_width(width);
        self.canvas.set_height(height);
        self.renderer.resize(width, height);
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
    let app = App::new(canvas.clone()).await?;
    let app = Rc::new(RefCell::new(app));

    // Set up keyboard handler (canvas needs focus for keyboard events)
    setup_keyboard_handler(app.clone(), &canvas)?;

    // Set up mouse handlers
    setup_mouse_handlers(app.clone(), &canvas)?;

    // Set up resize handler
    setup_resize_handler(app.clone())?;

    // Start animation loop
    start_animation_loop(app);

    Ok(())
}

/// Set up keyboard event handler.
fn setup_keyboard_handler(app: Rc<RefCell<App>>, _canvas: &HtmlCanvasElement) -> Result<(), String> {
    let window = web_sys::window().ok_or("No window")?;
    let document = window.document().ok_or("No document")?;

    // Add keyboard handler to document (more reliable than canvas)
    let handler = Closure::wrap(Box::new(move |event: KeyboardEvent| {
        // Ignore if user is typing in an input field
        if let Some(target) = event.target() {
            if let Ok(element) = target.dyn_into::<web_sys::Element>() {
                let tag = element.tag_name().to_uppercase();
                if tag == "INPUT" || tag == "TEXTAREA" {
                    return;
                }
            }
        }

        let key = event.key();
        log::info!("Key pressed: {}", key);
        
        // Prevent default for our handled keys to avoid browser shortcuts
        match key.to_uppercase().as_str() {
            "T" | "M" | "E" | "C" | "P" | "R" | "D" | "+" | "=" | "-" | "_" => {
                event.prevent_default();
            }
            _ => {}
        }
        
        app.borrow_mut().handle_key(&key);
    }) as Box<dyn FnMut(KeyboardEvent)>);

    document
        .add_event_listener_with_callback("keydown", handler.as_ref().unchecked_ref())
        .map_err(|_| "Failed to add keydown listener")?;

    handler.forget();
    log::info!("Keyboard handler registered on document");

    Ok(())
}

/// Set up mouse event handlers.
fn setup_mouse_handlers(app: Rc<RefCell<App>>, canvas: &HtmlCanvasElement) -> Result<(), String> {
    // Mouse wheel (zoom)
    let app_wheel = app.clone();
    let wheel_handler = Closure::wrap(Box::new(move |event: WheelEvent| {
        event.prevent_default();
        app_wheel.borrow_mut().handle_wheel(event.delta_y());
    }) as Box<dyn FnMut(WheelEvent)>);
    canvas
        .add_event_listener_with_callback("wheel", wheel_handler.as_ref().unchecked_ref())
        .map_err(|_| "Failed to add wheel listener")?;
    wheel_handler.forget();

    // Mouse down (also focuses canvas for keyboard events)
    let app_down = app.clone();
    let canvas_for_focus = canvas.clone();
    let mousedown_handler = Closure::wrap(Box::new(move |event: MouseEvent| {
        // Focus the canvas so keyboard events work
        let _ = canvas_for_focus.focus();
        app_down.borrow_mut().handle_mouse_down(event.offset_x() as f32, event.offset_y() as f32);
    }) as Box<dyn FnMut(MouseEvent)>);
    canvas
        .add_event_listener_with_callback("mousedown", mousedown_handler.as_ref().unchecked_ref())
        .map_err(|_| "Failed to add mousedown listener")?;
    mousedown_handler.forget();

    // Mouse move
    let app_move = app.clone();
    let mousemove_handler = Closure::wrap(Box::new(move |event: MouseEvent| {
        app_move.borrow_mut().handle_mouse_move(event.offset_x() as f32, event.offset_y() as f32);
    }) as Box<dyn FnMut(MouseEvent)>);
    canvas
        .add_event_listener_with_callback("mousemove", mousemove_handler.as_ref().unchecked_ref())
        .map_err(|_| "Failed to add mousemove listener")?;
    mousemove_handler.forget();

    // Mouse up
    let app_up = app.clone();
    let mouseup_handler = Closure::wrap(Box::new(move |_event: MouseEvent| {
        app_up.borrow_mut().handle_mouse_up();
    }) as Box<dyn FnMut(MouseEvent)>);
    canvas
        .add_event_listener_with_callback("mouseup", mouseup_handler.as_ref().unchecked_ref())
        .map_err(|_| "Failed to add mouseup listener")?;
    mouseup_handler.forget();

    // Mouse leave (also end drag)
    let app_leave = app.clone();
    let mouseleave_handler = Closure::wrap(Box::new(move |_event: MouseEvent| {
        app_leave.borrow_mut().handle_mouse_up();
    }) as Box<dyn FnMut(MouseEvent)>);
    canvas
        .add_event_listener_with_callback("mouseleave", mouseleave_handler.as_ref().unchecked_ref())
        .map_err(|_| "Failed to add mouseleave listener")?;
    mouseleave_handler.forget();

    Ok(())
}

/// Set up window resize handler.
fn setup_resize_handler(app: Rc<RefCell<App>>) -> Result<(), String> {
    let window = web_sys::window().ok_or("No window")?;

    let handler = Closure::wrap(Box::new(move |_event: web_sys::Event| {
        if let Some(window) = web_sys::window() {
            if let Some(document) = window.document() {
                if let Some(container) = document.get_element_by_id("canvas-container") {
                    let rect = container.get_bounding_client_rect();
                    let width = rect.width() as u32;
                    let height = rect.height() as u32;
                    if width > 0 && height > 0 {
                        app.borrow_mut().handle_resize(width, height);
                    }
                }
            }
        }
    }) as Box<dyn FnMut(web_sys::Event)>);

    window
        .add_event_listener_with_callback("resize", handler.as_ref().unchecked_ref())
        .map_err(|_| "Failed to add resize listener")?;

    handler.forget();
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

// Helper functions to update HUD elements

fn update_colormap_display(name: &str) {
    if let Some(window) = web_sys::window() {
        if let Some(document) = window.document() {
            // Update debug overlay
            if let Some(el) = document.get_element_by_id("colormap-display") {
                el.set_text_content(Some(name));
            }
            // Update footer
            if let Some(el) = document.get_element_by_id("colormap-display-footer") {
                el.set_text_content(Some(name));
            }
        }
    }
}

fn update_gain_display(gain: f32) {
    let text = format!("{:.1}x", gain);
    if let Some(window) = web_sys::window() {
        if let Some(document) = window.document() {
            // Update debug overlay
            if let Some(el) = document.get_element_by_id("gain-display") {
                el.set_text_content(Some(&text));
            }
            // Update footer
            if let Some(el) = document.get_element_by_id("gain-display-footer") {
                el.set_text_content(Some(&text));
            }
        }
    }
}

fn update_zoom_display(zoom: f32) {
    let text = format!("{:.1}x", zoom);
    if let Some(window) = web_sys::window() {
        if let Some(document) = window.document() {
            // Update debug overlay
            if let Some(el) = document.get_element_by_id("zoom-display") {
                el.set_text_content(Some(&text));
            }
            // Update footer
            if let Some(el) = document.get_element_by_id("zoom-display-footer") {
                el.set_text_content(Some(&text));
            }
        }
    }
}

fn toggle_debug_overlay(show: bool) {
    if let Some(window) = web_sys::window() {
        if let Some(document) = window.document() {
            if let Some(el) = document.get_element_by_id("debug-overlay") {
                if show {
                    let _ = el.class_list().remove_1("hidden");
                } else {
                    let _ = el.class_list().add_1("hidden");
                }
            }
        }
    }
}

fn show_toast(message: &str) {
    if let Some(window) = web_sys::window() {
        if let Some(document) = window.document() {
            if let Some(toast) = document.get_element_by_id("toast") {
                toast.set_text_content(Some(message));
                let _ = toast.class_list().remove_1("hidden");

                // Hide after 3 seconds
                let toast_clone = toast.clone();
                let hide_closure = Closure::once(Box::new(move || {
                    let _ = toast_clone.class_list().add_1("hidden");
                }) as Box<dyn FnOnce()>);

                let _ = window.set_timeout_with_callback_and_timeout_and_arguments_0(
                    hide_closure.as_ref().unchecked_ref(),
                    3000,
                );
                hide_closure.forget();
            }
        }
    }
}

// Simple JSON parsing helpers (avoid serde dependency in WASM)

fn extract_json_string(json: &str, key: &str) -> Option<String> {
    let pattern = format!("\"{}\":\"", key);
    if let Some(start) = json.find(&pattern) {
        let start = start + pattern.len();
        if let Some(end) = json[start..].find('"') {
            return Some(json[start..start + end].to_string());
        }
    }
    None
}

fn extract_json_bool(json: &str, key: &str) -> Option<bool> {
    let pattern_true = format!("\"{}\":true", key);
    let pattern_false = format!("\"{}\":false", key);
    if json.contains(&pattern_true) {
        Some(true)
    } else if json.contains(&pattern_false) {
        Some(false)
    } else {
        None
    }
}
