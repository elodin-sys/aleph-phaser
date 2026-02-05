//! WebSocket client for receiving radar frames.

use crate::protocol::RadarFrame;
use futures::channel::mpsc;
use std::cell::RefCell;
use std::rc::Rc;
use wasm_bindgen::prelude::*;
use web_sys::{BinaryType, MessageEvent, WebSocket};

/// WebSocket connection state.
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum ConnectionState {
    Connecting,
    Connected,
    Disconnected,
    Error,
}

/// WebSocket client for receiving radar frames.
pub struct FrameClient {
    socket: WebSocket,
    state: Rc<RefCell<ConnectionState>>,
    frame_rx: mpsc::UnboundedReceiver<RadarFrame>,
}

impl FrameClient {
    /// Create a new WebSocket client connected to the server.
    pub fn new(url: &str) -> Result<Self, JsValue> {
        log::info!("Connecting to WebSocket: {}", url);

        let socket = WebSocket::new(url)?;
        socket.set_binary_type(BinaryType::Arraybuffer);

        let state = Rc::new(RefCell::new(ConnectionState::Connecting));
        let (frame_tx, frame_rx) = mpsc::unbounded();

        // Set up event handlers
        Self::setup_handlers(&socket, state.clone(), frame_tx)?;

        Ok(Self {
            socket,
            state,
            frame_rx,
        })
    }

    /// Set up WebSocket event handlers.
    fn setup_handlers(
        socket: &WebSocket,
        state: Rc<RefCell<ConnectionState>>,
        frame_tx: mpsc::UnboundedSender<RadarFrame>,
    ) -> Result<(), JsValue> {
        // onopen
        let state_clone = state.clone();
        let onopen = Closure::wrap(Box::new(move |_: web_sys::Event| {
            log::info!("WebSocket connected");
            *state_clone.borrow_mut() = ConnectionState::Connected;

            // Update UI
            if let Some(window) = web_sys::window() {
                if let Some(document) = window.document() {
                    if let Some(indicator) = document.get_element_by_id("status-indicator") {
                        let _ = indicator.class_list().add_1("connected");
                    }
                    if let Some(text) = document.get_element_by_id("status-text") {
                        text.set_text_content(Some("Connected"));
                    }
                }
            }
        }) as Box<dyn FnMut(_)>);
        socket.set_onopen(Some(onopen.as_ref().unchecked_ref()));
        onopen.forget();

        // onclose
        let state_clone = state.clone();
        let onclose = Closure::wrap(Box::new(move |_: web_sys::Event| {
            log::info!("WebSocket closed");
            *state_clone.borrow_mut() = ConnectionState::Disconnected;

            // Update UI
            if let Some(window) = web_sys::window() {
                if let Some(document) = window.document() {
                    if let Some(indicator) = document.get_element_by_id("status-indicator") {
                        let _ = indicator.class_list().remove_1("connected");
                    }
                    if let Some(text) = document.get_element_by_id("status-text") {
                        text.set_text_content(Some("Disconnected"));
                    }
                }
            }
        }) as Box<dyn FnMut(_)>);
        socket.set_onclose(Some(onclose.as_ref().unchecked_ref()));
        onclose.forget();

        // onerror
        let state_clone = state.clone();
        let onerror = Closure::wrap(Box::new(move |e: web_sys::Event| {
            log::error!("WebSocket error: {:?}", e);
            *state_clone.borrow_mut() = ConnectionState::Error;
        }) as Box<dyn FnMut(_)>);
        socket.set_onerror(Some(onerror.as_ref().unchecked_ref()));
        onerror.forget();

        // onmessage
        let onmessage = Closure::wrap(Box::new(move |event: MessageEvent| {
            if let Ok(buffer) = event.data().dyn_into::<js_sys::ArrayBuffer>() {
                let array = js_sys::Uint8Array::new(&buffer);
                let bytes = array.to_vec();

                if let Some(frame) = RadarFrame::from_bytes(&bytes) {
                    if frame_tx.unbounded_send(frame).is_err() {
                        log::warn!("Frame channel closed");
                    }
                } else {
                    log::warn!("Failed to parse frame ({} bytes)", bytes.len());
                }
            }
        }) as Box<dyn FnMut(_)>);
        socket.set_onmessage(Some(onmessage.as_ref().unchecked_ref()));
        onmessage.forget();

        Ok(())
    }

    /// Get current connection state.
    pub fn state(&self) -> ConnectionState {
        *self.state.borrow()
    }

    /// Try to receive the next frame (non-blocking).
    pub fn try_recv(&mut self) -> Option<RadarFrame> {
        match self.frame_rx.try_next() {
            Ok(Some(frame)) => Some(frame),
            _ => None,
        }
    }

    /// Close the WebSocket connection.
    pub fn close(&self) {
        let _ = self.socket.close();
    }
}

impl Drop for FrameClient {
    fn drop(&mut self) {
        self.close();
    }
}
