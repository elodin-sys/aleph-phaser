//! WebGPU Radar Visualization Client
//!
//! This is the WASM entry point for the browser-based radar visualization.

mod app;
mod protocol;
mod renderer;
mod websocket;

use wasm_bindgen::prelude::*;

/// Initialize and run the radar visualization app.
#[wasm_bindgen(start)]
pub async fn main() -> Result<(), JsValue> {
    // Set up panic hook for better error messages in console
    console_error_panic_hook::set_once();

    // Initialize logging
    console_log::init_with_level(log::Level::Info).expect("Failed to init logger");

    log::info!("Radar Web Client starting...");

    // Run the application
    if let Err(e) = app::run().await {
        log::error!("Application error: {:?}", e);
        return Err(JsValue::from_str(&format!("Application error: {:?}", e)));
    }

    Ok(())
}
