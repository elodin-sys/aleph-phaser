//! WebSocket client for bidirectional radar communication.
//!
//! - Receives binary messages (radar frames)
//! - Receives text messages (JSON state updates)
//! - Sends text messages (JSON commands)

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

/// WebSocket client for bidirectional radar communication.
pub struct FrameClient {
    socket: Rc<WebSocket>,
    state: Rc<RefCell<ConnectionState>>,
    frame_rx: mpsc::UnboundedReceiver<RadarFrame>,
    state_rx: mpsc::UnboundedReceiver<String>,
}

impl FrameClient {
    /// Create a new WebSocket client connected to the server.
    pub fn new(url: &str) -> Result<Self, JsValue> {
        log::info!("Connecting to WebSocket: {}", url);

        let socket = WebSocket::new(url)?;
        socket.set_binary_type(BinaryType::Arraybuffer);
        let socket = Rc::new(socket);

        let state = Rc::new(RefCell::new(ConnectionState::Connecting));
        let (frame_tx, frame_rx) = mpsc::unbounded();
        let (state_tx, state_rx) = mpsc::unbounded();

        // Set up event handlers
        Self::setup_handlers(&socket, state.clone(), frame_tx, state_tx)?;

        Ok(Self {
            socket,
            state,
            frame_rx,
            state_rx,
        })
    }

    /// Set up WebSocket event handlers.
    fn setup_handlers(
        socket: &WebSocket,
        state: Rc<RefCell<ConnectionState>>,
        frame_tx: mpsc::UnboundedSender<RadarFrame>,
        state_tx: mpsc::UnboundedSender<String>,
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

        // onmessage - handle both binary (frames) and text (state updates)
        let onmessage = Closure::wrap(Box::new(move |event: MessageEvent| {
            let data = event.data();

            // Check if it's binary (ArrayBuffer) or text (String)
            if let Ok(buffer) = data.clone().dyn_into::<js_sys::ArrayBuffer>() {
                // Binary message = radar frame
                let array = js_sys::Uint8Array::new(&buffer);
                let bytes = array.to_vec();

                if let Some(frame) = RadarFrame::from_bytes(&bytes) {
                    if frame_tx.unbounded_send(frame).is_err() {
                        log::warn!("Frame channel closed");
                    }
                } else {
                    log::warn!("Failed to parse frame ({} bytes)", bytes.len());
                }
            } else if let Some(text) = data.as_string() {
                // Text message = JSON state update
                log::debug!("Received state update: {}", text);
                if state_tx.unbounded_send(text).is_err() {
                    log::warn!("State channel closed");
                }
            }
        }) as Box<dyn FnMut(_)>);
        socket.set_onmessage(Some(onmessage.as_ref().unchecked_ref()));
        onmessage.forget();

        Ok(())
    }

    /// Get current connection state.
    #[allow(dead_code)] // Public API for checking connection status
    pub fn state(&self) -> ConnectionState {
        *self.state.borrow()
    }

    /// Try to receive the next frame (non-blocking).
    pub fn try_recv_frame(&mut self) -> Option<RadarFrame> {
        match self.frame_rx.try_next() {
            Ok(Some(frame)) => Some(frame),
            _ => None,
        }
    }

    /// Try to receive the next state update (non-blocking).
    pub fn try_recv_state(&mut self) -> Option<String> {
        match self.state_rx.try_next() {
            Ok(Some(state)) => Some(state),
            _ => None,
        }
    }

    /// Send a command to the server.
    pub fn send_command(&self, cmd: &str) {
        if *self.state.borrow() == ConnectionState::Connected {
            if let Err(e) = self.socket.send_with_str(cmd) {
                log::error!("Failed to send command: {:?}", e);
            } else {
                log::debug!("Sent command: {}", cmd);
            }
        } else {
            log::warn!("Cannot send command: not connected");
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
