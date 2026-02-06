//! Wire protocol types for decoding radar frames.
//!
//! This is a WASM-compatible re-implementation of the frame header
//! from radar-core, since PyO3 is not available in WASM.

/// Header for wire-format frames (32 bytes).
///
/// Must match the layout in libs/radar-core/src/protocol.rs.
#[derive(Debug, Clone, Copy)]
#[allow(dead_code)] // Fields are part of protocol spec, used for parsing
pub struct FrameHeader {
    /// Message type (0x01 = radar_frame).
    pub message_type: u8,
    /// Frame type (0x00 = range_doppler).
    pub frame_type: u8,
    /// Number of Doppler bins.
    pub n_doppler: u16,
    /// Number of range bins.
    pub n_range: u16,
    /// Value format (0=u8, 1=u16, 2=f32).
    pub value_format: u8,
    /// Flags (bit0=MTI enabled).
    pub flags: u8,
    /// Minimum scale value.
    pub scale_min: f32,
    /// Maximum scale value.
    pub scale_max: f32,
    /// Minimum range in meters.
    pub range_min_m: f32,
    /// Maximum range in meters.
    pub range_max_m: f32,
    /// Minimum Doppler in Hz.
    pub doppler_min_hz: f32,
    /// Maximum Doppler in Hz.
    pub doppler_max_hz: f32,
}

impl FrameHeader {
    /// Size of the header in bytes.
    pub const SIZE: usize = 32;

    /// Message type for radar frames.
    #[allow(dead_code)] // Protocol constant for validation
    pub const MESSAGE_TYPE_RADAR_FRAME: u8 = 0x01;

    /// Frame type for range-Doppler maps.
    #[allow(dead_code)] // Protocol constant for validation
    pub const FRAME_TYPE_RANGE_DOPPLER: u8 = 0x00;

    /// Flag bit for MTI enabled.
    #[allow(dead_code)] // Protocol constant for validation
    pub const FLAG_MTI_ENABLED: u8 = 0x01;

    /// Parse header from a byte slice.
    pub fn from_bytes(bytes: &[u8]) -> Option<Self> {
        if bytes.len() < Self::SIZE {
            return None;
        }

        // Manual parsing since we can't use transmute in WASM safely
        Some(Self {
            message_type: bytes[0],
            frame_type: bytes[1],
            n_doppler: u16::from_le_bytes([bytes[2], bytes[3]]),
            n_range: u16::from_le_bytes([bytes[4], bytes[5]]),
            value_format: bytes[6],
            flags: bytes[7],
            scale_min: f32::from_le_bytes([bytes[8], bytes[9], bytes[10], bytes[11]]),
            scale_max: f32::from_le_bytes([bytes[12], bytes[13], bytes[14], bytes[15]]),
            range_min_m: f32::from_le_bytes([bytes[16], bytes[17], bytes[18], bytes[19]]),
            range_max_m: f32::from_le_bytes([bytes[20], bytes[21], bytes[22], bytes[23]]),
            doppler_min_hz: f32::from_le_bytes([bytes[24], bytes[25], bytes[26], bytes[27]]),
            doppler_max_hz: f32::from_le_bytes([bytes[28], bytes[29], bytes[30], bytes[31]]),
        })
    }

    /// Check if MTI is enabled in flags.
    #[allow(dead_code)] // Available for future use
    pub fn mti_enabled(&self) -> bool {
        self.flags & Self::FLAG_MTI_ENABLED != 0
    }

    /// Calculate expected payload size in bytes.
    pub fn payload_size(&self) -> usize {
        let samples = self.n_doppler as usize * self.n_range as usize;
        match self.value_format {
            0 => samples,      // u8
            1 => samples * 2,  // u16
            2 => samples * 4,  // f32
            _ => 0,
        }
    }

    /// Total expected message size (header + payload).
    pub fn total_size(&self) -> usize {
        Self::SIZE + self.payload_size()
    }
}

/// Decoded radar frame.
#[derive(Debug)]
pub struct RadarFrame {
    /// Frame header with metadata.
    pub header: FrameHeader,
    /// Payload data (u8 intensity values).
    pub payload: Vec<u8>,
}

impl RadarFrame {
    /// Decode a frame from raw bytes.
    pub fn from_bytes(bytes: &[u8]) -> Option<Self> {
        let header = FrameHeader::from_bytes(bytes)?;

        if bytes.len() < header.total_size() {
            log::warn!(
                "Frame too small: {} < {}",
                bytes.len(),
                header.total_size()
            );
            return None;
        }

        let payload = bytes[FrameHeader::SIZE..header.total_size()].to_vec();

        Some(Self { header, payload })
    }

    /// Get frame dimensions.
    pub fn dimensions(&self) -> (usize, usize) {
        (self.header.n_doppler as usize, self.header.n_range as usize)
    }
}
