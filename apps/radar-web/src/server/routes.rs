//! HTTP API routes.

use axum::{extract::State, routing::get, Json, Router};
use radar_core::{RadarConfig, RadarMode};
use serde::Serialize;
use std::sync::Arc;

/// API state shared across handlers.
#[derive(Clone)]
pub struct ApiState {
    pub config: Arc<RadarConfig>,
}

/// Server status response.
#[derive(Serialize)]
pub struct StatusResponse {
    pub status: String,
    pub version: String,
}

/// Radar configuration response.
#[derive(Serialize)]
pub struct ConfigResponse {
    pub mode: String,
    pub center_freq_hz: u64,
    pub sample_rate_hz: u64,
    pub output_freq_hz: u64,
    pub chirp_bw_hz: f64,
    pub n_doppler: usize,
    pub n_range_full: usize,
    pub max_range_m: f64,
    pub max_doppler_hz: f64,
    pub range_resolution_m: f64,
}

/// Build API routes.
pub fn api_routes(config: Arc<RadarConfig>) -> Router {
    let state = ApiState { config };

    Router::new()
        .route("/api/status", get(status_handler))
        .route("/api/config", get(config_handler))
        .with_state(state)
}

/// Status endpoint handler.
async fn status_handler() -> Json<StatusResponse> {
    Json(StatusResponse {
        status: "ok".to_string(),
        version: env!("CARGO_PKG_VERSION").to_string(),
    })
}

/// Config endpoint handler.
async fn config_handler(State(state): State<ApiState>) -> Json<ConfigResponse> {
    let config = &state.config;

    let mode_str = match config.mode {
        RadarMode::Synthetic => "synthetic",
        RadarMode::Hardware => "hardware",
    };

    Json(ConfigResponse {
        mode: mode_str.to_string(),
        center_freq_hz: config.center_freq,
        sample_rate_hz: config.sample_rate,
        output_freq_hz: config.output_freq,
        chirp_bw_hz: config.chirp_bw,
        n_doppler: config.n_doppler,
        n_range_full: config.n_range_full(),
        max_range_m: config.max_range,
        max_doppler_hz: config.max_doppler(),
        range_resolution_m: config.range_resolution(),
    })
}
