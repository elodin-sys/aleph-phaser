//! Test pattern definitions for synthetic radar mode.

/// Available test patterns for synthetic mode.
///
/// These patterns are useful for:
/// - Validating coordinate mapping and axis orientation
/// - Testing color mapping and scale ranges
/// - Debugging display issues without hardware
/// - Simulating realistic radar scenarios
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum TestPattern {
    /// Animated targets with motion (default).
    Animated,
    /// Bright dots at corners with different intensities.
    CornerDots,
    /// Horizontal gradient (range axis).
    GradientH,
    /// Vertical gradient (Doppler axis).
    GradientV,
    /// Single centered target.
    CenterTarget,
    /// Regular grid pattern.
    Grid,
    /// Diagonal line from bottom-left to top-right.
    Diagonal,
    /// Checkerboard pattern.
    Checkerboard,
    /// Simulated HB100 at 3m, stationary.
    Hb100Stationary,
    /// Simulated HB100 moving toward radar.
    Hb100Walking,
    /// Simulated DC leakage artifact.
    DcLeakage,
}

impl TestPattern {
    /// All available test patterns in cycling order.
    pub const ALL: &'static [TestPattern] = &[
        Self::Animated,
        Self::CornerDots,
        Self::GradientH,
        Self::GradientV,
        Self::CenterTarget,
        Self::Grid,
        Self::Diagonal,
        Self::Checkerboard,
        Self::Hb100Stationary,
        Self::Hb100Walking,
        Self::DcLeakage,
    ];

    /// Get the string name of this pattern (matches Python backend).
    pub fn name(&self) -> &'static str {
        match self {
            Self::Animated => "animated",
            Self::CornerDots => "corner_dots",
            Self::GradientH => "gradient_h",
            Self::GradientV => "gradient_v",
            Self::CenterTarget => "center_target",
            Self::Grid => "grid",
            Self::Diagonal => "diagonal",
            Self::Checkerboard => "checkerboard",
            Self::Hb100Stationary => "hb100_stationary",
            Self::Hb100Walking => "hb100_walking",
            Self::DcLeakage => "dc_leakage",
        }
    }

    /// Parse a pattern from its string name.
    pub fn from_name(name: &str) -> Option<Self> {
        Self::ALL.iter().find(|p| p.name() == name).copied()
    }

    /// Get the next pattern in the cycle.
    pub fn next(&self) -> Self {
        let idx = Self::ALL
            .iter()
            .position(|p| p == self)
            .unwrap_or(0);
        Self::ALL[(idx + 1) % Self::ALL.len()]
    }

    /// Get the previous pattern in the cycle.
    pub fn prev(&self) -> Self {
        let idx = Self::ALL
            .iter()
            .position(|p| p == self)
            .unwrap_or(0);
        if idx == 0 {
            Self::ALL[Self::ALL.len() - 1]
        } else {
            Self::ALL[idx - 1]
        }
    }

    /// Get a human-readable description of the pattern.
    pub fn description(&self) -> &'static str {
        match self {
            Self::Animated => "Animated moving targets",
            Self::CornerDots => "Corner dots with different intensities",
            Self::GradientH => "Horizontal gradient (range axis)",
            Self::GradientV => "Vertical gradient (Doppler axis)",
            Self::CenterTarget => "Single centered Gaussian target",
            Self::Grid => "Regular grid pattern",
            Self::Diagonal => "Diagonal line bottom-left to top-right",
            Self::Checkerboard => "Checkerboard pattern",
            Self::Hb100Stationary => "Simulated HB100 at 3m, stationary",
            Self::Hb100Walking => "Simulated HB100 approaching at walking speed",
            Self::DcLeakage => "Simulated DC leakage artifact",
        }
    }
}

impl Default for TestPattern {
    fn default() -> Self {
        Self::Animated
    }
}

impl std::fmt::Display for TestPattern {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.name())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_pattern_names() {
        assert_eq!(TestPattern::Animated.name(), "animated");
        assert_eq!(TestPattern::CornerDots.name(), "corner_dots");
    }

    #[test]
    fn test_pattern_from_name() {
        assert_eq!(
            TestPattern::from_name("animated"),
            Some(TestPattern::Animated)
        );
        assert_eq!(TestPattern::from_name("invalid"), None);
    }

    #[test]
    fn test_pattern_cycling() {
        let p = TestPattern::Animated;
        let next = p.next();
        assert_eq!(next, TestPattern::CornerDots);
        assert_eq!(next.prev(), p);
    }

    #[test]
    fn test_pattern_cycle_wraps() {
        let last = TestPattern::DcLeakage;
        assert_eq!(last.next(), TestPattern::Animated);
        assert_eq!(TestPattern::Animated.prev(), TestPattern::DcLeakage);
    }
}
