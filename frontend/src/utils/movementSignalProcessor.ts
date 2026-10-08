/**
 * Movement Signal Processor for MediaPipe Pose Telemetry
 * Preserves genuine human movement and anatomical geometry.
 * 
 * Key Principles:
 * 1. Independent Left & Right leg processing - movements of one leg NEVER leak or mirror to the other.
 * 2. Adaptive temporal filtering - light EMA (alpha 0.70-0.85) during active motion to track genuine leg lifts/swings
 *    with zero lag or rotational drift; stronger smoothing only applied when stationary.
 * 3. Directional velocity extrapolation for short dropouts (<= 3 frames) without freezing or collapsing to wrong poses.
 * 4. Separate left/right outlier detection - angular speed clamped per knee, never forcing an artificial rotation.
 * 5. Explicit 2D/3D coordinate consistency - x (horizontal), y (vertical, down positive), z (depth) kept unswapped.
 */

export interface LandmarkPoint {
  x: number;
  y: number;
  z?: number;
  v: number;       // visibility / confidence [0, 1]
  normX: number;
  normY: number;
  normZ?: number;
  interpolated?: boolean;
}

export interface SmoothedPoseFrame {
  timestamp: number;
  rawLandmarks: {
    l_hip: LandmarkPoint;
    r_hip: LandmarkPoint;
    l_knee: LandmarkPoint;
    r_knee: LandmarkPoint;
    l_ankle: LandmarkPoint;
    r_ankle: LandmarkPoint;
  };
  landmarks: {
    l_shoulder: LandmarkPoint;
    r_shoulder: LandmarkPoint;
    l_hip: LandmarkPoint;
    r_hip: LandmarkPoint;
    l_knee: LandmarkPoint;
    r_knee: LandmarkPoint;
    l_ankle: LandmarkPoint;
    r_ankle: LandmarkPoint;
    l_heel?: LandmarkPoint | null;
    r_heel?: LandmarkPoint | null;
    l_foot?: LandmarkPoint | null;
    r_foot?: LandmarkPoint | null;
  };
  leftKneeAngle: number;
  rightKneeAngle: number;
  rawLeftKneeAngle: number;
  rawRightKneeAngle: number;
  leftMovementDirection: 'flexing' | 'extending' | 'stationary';
  rightMovementDirection: 'flexing' | 'extending' | 'stationary';
  isValid: boolean;
  isOutlier: boolean;
  phase: 'start' | 'flexion' | 'peak_flexion' | 'extension' | 'completion' | 'stationary';
  leftPhase: 'stationary' | 'flexion' | 'peak_flexion' | 'extension';
  rightPhase: 'stationary' | 'flexion' | 'peak_flexion' | 'extension';
}

export interface MovementTelemetryStats {
  totalFrames: number;
  validFrames: number;
  validFrameRatio: number;
  missingLandmarkFrames: number;
  outlierFramesCount: number;
  interpolatedFramesCount: number;
  landmarkQualityScore: number;   // 0 - 100
  jitterScore: number;            // average pixel jitter
  movementCompleted: boolean;
  completionScore: number;        // 0 - 100
  minLeftAngle: number;
  maxLeftAngle: number;
  minRightAngle: number;
  maxRightAngle: number;
  leftRom: number;
  rightRom: number;
  leftExcursion: number;
  rightExcursion: number;
  requiredExcursion: number;
  kneeSymmetry: number;
  framingStatus: string;
  userGuidance: string | null;
}

interface JointVelocity {
  vx: number;
  vy: number;
}

export class MovementSignalProcessor {
  // Configurable thresholds
  private readonly VISIBILITY_THRESHOLD = 0.50; // Landmark must have >= 0.5 confidence
  private readonly MAX_INTERPOLATION_GAP = 3;  // Max consecutive frames allowed to interpolate
  private readonly MAX_ANGULAR_VELOCITY_DEG_PER_SEC = 380; // Above 380 deg/s is camera jitter outlier
  private readonly MIN_ROM_COMPLETION_DEG = 25; // At least 25° active flexion to constitute completed movement

  // State buffers per joint
  private prevSmoothedLandmarks: Record<string, { x: number; y: number; normX: number; normY: number }> | null = null;
  private prevJointVelocities: Record<string, JointVelocity> = {};
  private prevSmoothedAngles: { left: number; right: number } | null = null;
  private prevTimestamp: number = 0;

  // Independent left/right missing frame counters
  private leftMissingCount: number = 0;
  private rightMissingCount: number = 0;
  private lastKnownGoodLeft: { hip: LandmarkPoint; knee: LandmarkPoint; ankle: LandmarkPoint } | null = null;
  private lastKnownGoodRight: { hip: LandmarkPoint; knee: LandmarkPoint; ankle: LandmarkPoint } | null = null;

  // Statistics accumulators
  private totalFrames: number = 0;
  private validFrames: number = 0;
  private missingFrames: number = 0;
  private outlierCount: number = 0;
  private interpolatedCount: number = 0;
  private confidenceSum: number = 0;
  private jitterSum: number = 0;
  private jitterSamples: number = 0;

  // Real movement bounds from validated filtered frames
  private leftAnglesHistory: number[] = [];
  private rightAnglesHistory: number[] = [];
  private phasesHistory: string[] = [];

  // Independent left / right motion tracking
  private leftBaselineStandingAngle: number = 0;
  private rightBaselineStandingAngle: number = 0;
  private leftDeepestFlexionAngle: number = 180;
  private rightDeepestFlexionAngle: number = 180;
  private leftReturnDetected: boolean = false;
  private rightReturnDetected: boolean = false;
  private movementPhase: 'start' | 'flexion' | 'peak_flexion' | 'extension' | 'completion' | 'stationary' = 'start';

  public reset(): void {
    this.prevSmoothedLandmarks = null;
    this.prevJointVelocities = {};
    this.prevSmoothedAngles = null;
    this.prevTimestamp = 0;
    this.leftMissingCount = 0;
    this.rightMissingCount = 0;
    this.lastKnownGoodLeft = null;
    this.lastKnownGoodRight = null;
    this.totalFrames = 0;
    this.validFrames = 0;
    this.missingFrames = 0;
    this.outlierCount = 0;
    this.interpolatedCount = 0;
    this.confidenceSum = 0;
    this.jitterSum = 0;
    this.jitterSamples = 0;
    this.leftAnglesHistory = [];
    this.rightAnglesHistory = [];
    this.phasesHistory = [];
    this.leftBaselineStandingAngle = 0;
    this.rightBaselineStandingAngle = 0;
    this.leftDeepestFlexionAngle = 180;
    this.rightDeepestFlexionAngle = 180;
    this.leftReturnDetected = false;
    this.rightReturnDetected = false;
    this.movementPhase = 'start';
  }

  /**
   * Calculates planar 2D angle between a - b - c in degrees [0, 180]
   * Preserves standard image coordinates: x horizontal, y vertical.
   */
  public calculateAngle(
    a: { x: number; y: number },
    b: { x: number; y: number },
    c: { x: number; y: number }
  ): number {
    const baX = a.x - b.x;
    const baY = a.y - b.y;
    const bcX = c.x - b.x;
    const bcY = c.y - b.y;
    const dot = baX * bcX + baY * bcY;
    const magBA = Math.sqrt(baX * baX + baY * baY);
    const magBC = Math.sqrt(bcX * bcX + bcY * bcY);
    if (magBA === 0 || magBC === 0) return 180;
    const cosAngle = Math.max(-1, Math.min(1, dot / (magBA * magBC)));
    return Math.round((Math.acos(cosAngle) * 180) / Math.PI);
  }

  /**
   * Process a single video frame containing raw landmarks from MediaPipe Pose.
   * Completely preserves genuine independent movement of each leg.
   */
  public processFrame(
    rawLm: any[],
    width: number,
    height: number,
    timestamp: number
  ): SmoothedPoseFrame {
    this.totalFrames += 1;
    const dtSec = this.prevTimestamp > 0 ? Math.max(0.01, (timestamp - this.prevTimestamp) / 1000) : 0.033;
    this.prevTimestamp = timestamp;

    const toPoint = (idx: number): LandmarkPoint => {
      if (!rawLm || !rawLm[idx]) {
        return { x: 0, y: 0, z: 0, v: 0, normX: 0, normY: 0, normZ: 0 };
      }
      return {
        x: rawLm[idx].x * width,
        y: rawLm[idx].y * height,
        z: rawLm[idx].z !== undefined ? rawLm[idx].z * width : 0,
        v: rawLm[idx].visibility !== undefined ? rawLm[idx].visibility : 0.9,
        normX: rawLm[idx].x,
        normY: rawLm[idx].y,
        normZ: rawLm[idx].z || 0
      };
    };

    // Extract core joints without modifying coordinates
    const l_shoulder = toPoint(11);
    const r_shoulder = toPoint(12);
    let l_hip = toPoint(23);
    let r_hip = toPoint(24);
    let l_knee = toPoint(25);
    let r_knee = toPoint(26);
    let l_ankle = toPoint(27);
    let r_ankle = toPoint(28);
    const l_heel = rawLm.length > 29 ? toPoint(29) : null;
    const r_heel = rawLm.length > 30 ? toPoint(30) : null;
    const l_foot = rawLm.length > 31 ? toPoint(31) : null;
    const r_foot = rawLm.length > 32 ? toPoint(32) : null;

    // Retain clean raw snapshot for side-by-side debug comparison
    const rawSnapshot = {
      l_hip: { ...l_hip },
      r_hip: { ...r_hip },
      l_knee: { ...l_knee },
      r_knee: { ...r_knee },
      l_ankle: { ...l_ankle },
      r_ankle: { ...r_ankle }
    };

    // Calculate raw knee angles directly before any processing
    const rawLeftKneeAngle = this.calculateAngle(l_hip, l_knee, l_ankle);
    const rawRightKneeAngle = this.calculateAngle(r_hip, r_knee, r_ankle);

    // Mean landmark confidence across lower extremities
    const coreJoints = [l_shoulder, r_shoulder, l_hip, r_hip, l_knee, r_knee, l_ankle, r_ankle];
    const meanConf = coreJoints.reduce((sum, p) => sum + p.v, 0) / coreJoints.length;
    this.confidenceSum += meanConf;

    // INDEPENDENT Left & Right leg confidence evaluations
    const leftMissing = (
      l_hip.v < this.VISIBILITY_THRESHOLD ||
      l_knee.v < this.VISIBILITY_THRESHOLD ||
      l_ankle.v < this.VISIBILITY_THRESHOLD
    );

    const rightMissing = (
      r_hip.v < this.VISIBILITY_THRESHOLD ||
      r_knee.v < this.VISIBILITY_THRESHOLD ||
      r_ankle.v < this.VISIBILITY_THRESHOLD
    );

    let leftInterpolated = false;
    let rightInterpolated = false;

    // --- LEFT LEG INTERPOLATION (Independent) ---
    if (leftMissing) {
      this.leftMissingCount += 1;
      this.missingFrames += 1;
      if (this.leftMissingCount <= this.MAX_INTERPOLATION_GAP && this.lastKnownGoodLeft) {
        // Safe trajectory velocity extrapolation:
        const vKnee = this.prevJointVelocities['l_knee'] || { vx: 0, vy: 0 };
        const vAnkle = this.prevJointVelocities['l_ankle'] || { vx: 0, vy: 0 };

        // Extrapolate at dampening rate (0.6x velocity) so joint doesn't freeze or collapse
        l_hip = { ...this.lastKnownGoodLeft.hip, v: 0.55, interpolated: true };
        l_knee = {
          ...this.lastKnownGoodLeft.knee,
          x: this.lastKnownGoodLeft.knee.x + vKnee.vx * dtSec * 0.6,
          y: this.lastKnownGoodLeft.knee.y + vKnee.vy * dtSec * 0.6,
          normX: (this.lastKnownGoodLeft.knee.x + vKnee.vx * dtSec * 0.6) / width,
          normY: (this.lastKnownGoodLeft.knee.y + vKnee.vy * dtSec * 0.6) / height,
          v: 0.55,
          interpolated: true
        };
        l_ankle = {
          ...this.lastKnownGoodLeft.ankle,
          x: this.lastKnownGoodLeft.ankle.x + vAnkle.vx * dtSec * 0.6,
          y: this.lastKnownGoodLeft.ankle.y + vAnkle.vy * dtSec * 0.6,
          normX: (this.lastKnownGoodLeft.ankle.x + vAnkle.vx * dtSec * 0.6) / width,
          normY: (this.lastKnownGoodLeft.ankle.y + vAnkle.vy * dtSec * 0.6) / height,
          v: 0.55,
          interpolated: true
        };
        leftInterpolated = true;
        this.interpolatedCount += 1;
      }
    } else {
      this.leftMissingCount = 0;
      this.lastKnownGoodLeft = { hip: { ...l_hip }, knee: { ...l_knee }, ankle: { ...l_ankle } };
    }

    // --- RIGHT LEG INTERPOLATION (Independent) ---
    if (rightMissing) {
      this.rightMissingCount += 1;
      this.missingFrames += 1;
      if (this.rightMissingCount <= this.MAX_INTERPOLATION_GAP && this.lastKnownGoodRight) {
        const vKnee = this.prevJointVelocities['r_knee'] || { vx: 0, vy: 0 };
        const vAnkle = this.prevJointVelocities['r_ankle'] || { vx: 0, vy: 0 };

        r_hip = { ...this.lastKnownGoodRight.hip, v: 0.55, interpolated: true };
        r_knee = {
          ...this.lastKnownGoodRight.knee,
          x: this.lastKnownGoodRight.knee.x + vKnee.vx * dtSec * 0.6,
          y: this.lastKnownGoodRight.knee.y + vKnee.vy * dtSec * 0.6,
          normX: (this.lastKnownGoodRight.knee.x + vKnee.vx * dtSec * 0.6) / width,
          normY: (this.lastKnownGoodRight.knee.y + vKnee.vy * dtSec * 0.6) / height,
          v: 0.55,
          interpolated: true
        };
        r_ankle = {
          ...this.lastKnownGoodRight.ankle,
          x: this.lastKnownGoodRight.ankle.x + vAnkle.vx * dtSec * 0.6,
          y: this.lastKnownGoodRight.ankle.y + vAnkle.vy * dtSec * 0.6,
          normX: (this.lastKnownGoodRight.ankle.x + vAnkle.vx * dtSec * 0.6) / width,
          normY: (this.lastKnownGoodRight.ankle.y + vAnkle.vy * dtSec * 0.6) / height,
          v: 0.55,
          interpolated: true
        };
        rightInterpolated = true;
        this.interpolatedCount += 1;
      }
    } else {
      this.rightMissingCount = 0;
      this.lastKnownGoodRight = { hip: { ...r_hip }, knee: { ...r_knee }, ankle: { ...r_ankle } };
    }

    // --- ADAPTIVE VELOCITY-AWARE TEMPORAL SMOOTHING ---
    // High alpha (0.80 - 0.90) during genuine motion to track lifts & swings without delay;
    // Lower alpha (0.50) when resting/stationary to eliminate camera micro-jitter.
    const smoothPt = (curr: LandmarkPoint, key: string): LandmarkPoint => {
      if (!this.prevSmoothedLandmarks || !this.prevSmoothedLandmarks[key]) {
        this.prevJointVelocities[key] = { vx: 0, vy: 0 };
        return curr;
      }
      const prev = this.prevSmoothedLandmarks[key];
      const dx = curr.x - prev.x;
      const dy = curr.y - prev.y;
      const speed = Math.hypot(dx, dy) / Math.max(0.001, dtSec);

      // Track joint velocity
      this.prevJointVelocities[key] = {
        vx: dx / Math.max(0.001, dtSec),
        vy: dy / Math.max(0.001, dtSec)
      };

      // Adaptive Alpha:
      // If speed > 100 px/sec (clear human limb swing), use alpha = 0.85 (ultra responsive, zero rotation/drag)
      // If speed < 20 px/sec (stationary limb), use alpha = 0.50 (cleans camera noise)
      let alpha = 0.55;
      if (speed > 120) {
        alpha = 0.85;
      } else if (speed > 40) {
        alpha = 0.55 + ((speed - 40) / 80) * 0.30;
      }

      const smX = alpha * curr.x + (1 - alpha) * prev.x;
      const smY = alpha * curr.y + (1 - alpha) * prev.y;
      const smNormX = alpha * curr.normX + (1 - alpha) * prev.normX;
      const smNormY = alpha * curr.normY + (1 - alpha) * prev.normY;

      return {
        x: smX,
        y: smY,
        z: curr.z,
        v: curr.v,
        normX: smNormX,
        normY: smNormY,
        normZ: curr.normZ,
        interpolated: curr.interpolated
      };
    };

    const sm_l_hip = smoothPt(l_hip, 'l_hip');
    const sm_r_hip = smoothPt(r_hip, 'r_hip');
    const sm_l_knee = smoothPt(l_knee, 'l_knee');
    const sm_r_knee = smoothPt(r_knee, 'r_knee');
    const sm_l_ankle = smoothPt(l_ankle, 'l_ankle');
    const sm_r_ankle = smoothPt(r_ankle, 'r_ankle');

    // Calculate frame jitter for telemetry
    if (this.prevSmoothedLandmarks) {
      const pL = this.prevSmoothedLandmarks['l_knee'];
      const pR = this.prevSmoothedLandmarks['r_knee'];
      const dL = Math.hypot(sm_l_knee.x - pL.x, sm_l_knee.y - pL.y);
      const dR = Math.hypot(sm_r_knee.x - pR.x, sm_r_knee.y - pR.y);
      this.jitterSum += (dL + dR) / 2;
      this.jitterSamples += 1;
    }

    this.prevSmoothedLandmarks = {
      l_hip: { x: sm_l_hip.x, y: sm_l_hip.y, normX: sm_l_hip.normX, normY: sm_l_hip.normY },
      r_hip: { x: sm_r_hip.x, y: sm_r_hip.y, normX: sm_r_hip.normX, normY: sm_r_hip.normY },
      l_knee: { x: sm_l_knee.x, y: sm_l_knee.y, normX: sm_l_knee.normX, normY: sm_l_knee.normY },
      r_knee: { x: sm_r_knee.x, y: sm_r_knee.y, normX: sm_r_knee.normX, normY: sm_r_knee.normY },
      l_ankle: { x: sm_l_ankle.x, y: sm_l_ankle.y, normX: sm_l_ankle.normX, normY: sm_l_ankle.normY },
      r_ankle: { x: sm_r_ankle.x, y: sm_r_ankle.y, normX: sm_r_ankle.normX, normY: sm_r_ankle.normY }
    };

    // Calculate Knee Angles from Hip -> Knee -> Ankle
    let leftAngle = this.calculateAngle(sm_l_hip, sm_l_knee, sm_l_ankle);
    let rightAngle = this.calculateAngle(sm_r_hip, sm_r_knee, sm_r_ankle);

    // Independent Outlier Rejection per knee (preserving the other leg completely)
    let isOutlier = false;
    if (this.prevSmoothedAngles && dtSec > 0) {
      const velLeft = Math.abs(leftAngle - this.prevSmoothedAngles.left) / dtSec;
      const velRight = Math.abs(rightAngle - this.prevSmoothedAngles.right) / dtSec;
      const maxDelta = this.MAX_ANGULAR_VELOCITY_DEG_PER_SEC * dtSec;

      if (velLeft > this.MAX_ANGULAR_VELOCITY_DEG_PER_SEC) {
        isOutlier = true;
        this.outlierCount += 1;
        leftAngle = Math.round(
          this.prevSmoothedAngles.left + Math.sign(leftAngle - this.prevSmoothedAngles.left) * maxDelta
        );
      }

      if (velRight > this.MAX_ANGULAR_VELOCITY_DEG_PER_SEC) {
        isOutlier = true;
        this.outlierCount += 1;
        rightAngle = Math.round(
          this.prevSmoothedAngles.right + Math.sign(rightAngle - this.prevSmoothedAngles.right) * maxDelta
        );
      }
    }

    // Physiological bounds clamp [30°, 180°]
    leftAngle = Math.max(30, Math.min(180, leftAngle));
    rightAngle = Math.max(30, Math.min(180, rightAngle));

    // Direction tracking per leg
    let leftDirection: 'flexing' | 'extending' | 'stationary' = 'stationary';
    let rightDirection: 'flexing' | 'extending' | 'stationary' = 'stationary';
    if (this.prevSmoothedAngles) {
      const dL = leftAngle - this.prevSmoothedAngles.left;
      const dR = rightAngle - this.prevSmoothedAngles.right;
      if (dL < -2) leftDirection = 'flexing';
      else if (dL > 2) leftDirection = 'extending';

      if (dR < -2) rightDirection = 'flexing';
      else if (dR > 2) rightDirection = 'extending';
    }

    this.prevSmoothedAngles = { left: leftAngle, right: rightAngle };

    // Independent Framing Checks
    const outOfBounds = (
      sm_l_knee.normX < 0.04 || sm_l_knee.normX > 0.96 || sm_l_knee.normY < 0.05 || sm_l_knee.normY > 0.98 ||
      sm_r_knee.normX < 0.04 || sm_r_knee.normX > 0.96 || sm_r_knee.normY < 0.05 || sm_r_knee.normY > 0.98 ||
      sm_l_ankle.normX < 0.04 || sm_l_ankle.normX > 0.96 || sm_l_ankle.normY < 0.05 || sm_l_ankle.normY > 0.98
    );

    const hasCriticalMissing = leftMissing || rightMissing;
    const isFrameValid = !hasCriticalMissing && !outOfBounds && !isOutlier;
    if (isFrameValid) {
      this.validFrames += 1;
      this.leftAnglesHistory.push(leftAngle);
      this.rightAnglesHistory.push(rightAngle);
    }

    // --- INDEPENDENT MOVEMENT-PHASE TRACKING ---
    // Left & Right Leg Baseline Initialization & Adaptive Tracking:
    // Update baseline whenever in an extended posture (angle >= 150°) or during initial frames
    if (isFrameValid) {
      if (this.leftBaselineStandingAngle === 0) {
        this.leftBaselineStandingAngle = leftAngle;
      } else if (leftAngle >= 150 && leftAngle > this.leftBaselineStandingAngle) {
        this.leftBaselineStandingAngle = leftAngle;
      }

      if (this.rightBaselineStandingAngle === 0) {
        this.rightBaselineStandingAngle = rightAngle;
      } else if (rightAngle >= 150 && rightAngle > this.rightBaselineStandingAngle) {
        this.rightBaselineStandingAngle = rightAngle;
      }
    }

    // Left Leg Phase
    let leftPhase: 'stationary' | 'flexion' | 'peak_flexion' | 'extension' = 'stationary';

    if (leftAngle < this.leftDeepestFlexionAngle && isFrameValid) {
      this.leftDeepestFlexionAngle = leftAngle;
    }
    if (rightAngle < this.rightDeepestFlexionAngle && isFrameValid) {
      this.rightDeepestFlexionAngle = rightAngle;
    }

    const lDeficit = this.leftBaselineStandingAngle - leftAngle;
    if (lDeficit < 8) {
      leftPhase = 'stationary';
    } else if (lDeficit >= this.MIN_ROM_COMPLETION_DEG && leftAngle <= this.leftDeepestFlexionAngle + 4) {
      leftPhase = 'peak_flexion';
      this.leftReturnDetected = true;
    } else if (this.leftReturnDetected) {
      leftPhase = 'extension';
    } else {
      leftPhase = 'flexion';
    }

    // Right Leg Phase
    let rightPhase: 'stationary' | 'flexion' | 'peak_flexion' | 'extension' = 'stationary';
    const rDeficit = this.rightBaselineStandingAngle - rightAngle;
    if (rDeficit < 8) {
      rightPhase = 'stationary';
    } else if (rDeficit >= this.MIN_ROM_COMPLETION_DEG && rightAngle <= this.rightDeepestFlexionAngle + 4) {
      rightPhase = 'peak_flexion';
      this.rightReturnDetected = true;
    } else if (this.rightReturnDetected) {
      rightPhase = 'extension';
    } else {
      rightPhase = 'flexion';
    }

    // Overall session phase (driven by the active limb)
    const activeDeficit = Math.max(lDeficit, rDeficit);
    if (activeDeficit < 8) {
      const activeCompleted = (
        (this.leftDeepestFlexionAngle < (this.leftBaselineStandingAngle - this.MIN_ROM_COMPLETION_DEG) && this.leftReturnDetected) ||
        (this.rightDeepestFlexionAngle < (this.rightBaselineStandingAngle - this.MIN_ROM_COMPLETION_DEG) && this.rightReturnDetected)
      );
      this.movementPhase = activeCompleted ? 'completion' : 'stationary';
    } else if (leftPhase === 'peak_flexion' || rightPhase === 'peak_flexion') {
      this.movementPhase = 'peak_flexion';
    } else if (leftPhase === 'extension' || rightPhase === 'extension') {
      this.movementPhase = 'extension';
    } else {
      this.movementPhase = 'flexion';
    }
    this.phasesHistory.push(this.movementPhase);

    return {
      timestamp,
      rawLandmarks: rawSnapshot,
      landmarks: {
        l_shoulder,
        r_shoulder,
        l_hip: sm_l_hip,
        r_hip: sm_r_hip,
        l_knee: sm_l_knee,
        r_knee: sm_r_knee,
        l_ankle: sm_l_ankle,
        r_ankle: sm_r_ankle,
        l_heel,
        r_heel,
        l_foot,
        r_foot
      },
      leftKneeAngle: leftAngle,
      rightKneeAngle: rightAngle,
      rawLeftKneeAngle,
      rawRightKneeAngle,
      leftMovementDirection: leftDirection,
      rightMovementDirection: rightDirection,
      isValid: isFrameValid,
      isOutlier,
      phase: this.movementPhase,
      leftPhase,
      rightPhase
    };
  }

  /**
   * Evaluates camera/person framing quality and provides clear user guidance
   */
  public getFramingEvaluation(): { framingStatus: string; userGuidance: string | null } {
    if (this.totalFrames === 0) {
      return { framingStatus: 'No Pose Detected', userGuidance: 'Please step directly into camera view.' };
    }

    const validRatio = this.totalFrames > 0 ? this.validFrames / this.totalFrames : 0;
    const avgConf = this.totalFrames > 0 ? (this.confidenceSum / this.totalFrames) * 100 : 0;

    if (avgConf < 50) {
      return { framingStatus: 'Poor Visibility', userGuidance: 'Low lighting or occluded view. Please step into a well-lit area.' };
    }
    if (validRatio < 0.60) {
      return { framingStatus: 'Occluded Landmarks', userGuidance: 'Please keep both knees and ankles clearly visible throughout.' };
    }
    if (this.leftMissingCount > 2 || this.rightMissingCount > 2) {
      return { framingStatus: 'Landmark Dropout', userGuidance: 'Please ensure feet and knees remain inside the camera frame.' };
    }
    return { framingStatus: 'Optimal Framing', userGuidance: null };
  }

  /**
   * Computes comprehensive movement telemetry statistics
   */
  public getTelemetryStats(): MovementTelemetryStats {
    const validRatio = this.totalFrames > 0 ? Number((this.validFrames / this.totalFrames).toFixed(3)) : 0;
    const avgConfidence = this.totalFrames > 0 ? Math.round((this.confidenceSum / this.totalFrames) * 100) : 0;
    const avgJitter = this.jitterSamples > 0 ? Number((this.jitterSum / this.jitterSamples).toFixed(2)) : 0;

    // Movement completion: verified if either leg underwent active excursion and returned
    const leftExcursion = Math.max(0, this.leftBaselineStandingAngle - this.leftDeepestFlexionAngle);
    const rightExcursion = Math.max(0, this.rightBaselineStandingAngle - this.rightDeepestFlexionAngle);
    const maxExcursion = Math.max(leftExcursion, rightExcursion);

    const movementCompleted = (
      this.validFrames >= 15 &&
      maxExcursion >= this.MIN_ROM_COMPLETION_DEG &&
      (this.movementPhase === 'completion' || this.leftReturnDetected || this.rightReturnDetected)
    );

    const completionScore = movementCompleted
      ? Math.min(100, Math.round((validRatio * 60) + (Math.min(1, maxExcursion / 70) * 40)))
      : Math.round(validRatio * 40);

    // Calculate robust knee ROM using 5th and 95th percentiles of validated history
    let minLeft = 180, maxLeft = 180, minRight = 180, maxRight = 180;
    let leftRom = 120, rightRom = 120;

    if (this.leftAnglesHistory.length >= 5) {
      const sortedL = [...this.leftAnglesHistory].sort((a, b) => a - b);
      const sortedR = [...this.rightAnglesHistory].sort((a, b) => a - b);
      const p05L = sortedL[Math.floor(sortedL.length * 0.05)];
      const p95L = sortedL[Math.floor(sortedL.length * 0.95)];
      const p05R = sortedR[Math.floor(sortedR.length * 0.05)];
      const p95R = sortedR[Math.floor(sortedR.length * 0.95)];

      minLeft = p05L;
      maxLeft = p95L;
      minRight = p05R;
      maxRight = p95R;
      // ROM represents full physiological excursion observed in session:
      // take maximum of percentile span and the verified peak excursion
      leftRom = Math.max(10, Math.max(maxLeft - minLeft, leftExcursion));
      rightRom = Math.max(10, Math.max(maxRight - minRight, rightExcursion));
    } else {
      leftRom = Math.max(10, leftExcursion);
      rightRom = Math.max(10, rightExcursion);
    }

    const maxRom = Math.max(leftRom, rightRom);
    const kneeSym = maxRom > 0 ? Math.round(100 - (Math.abs(leftRom - rightRom) / maxRom) * 100) : 100;
    const framing = this.getFramingEvaluation();

    return {
      totalFrames: this.totalFrames,
      validFrames: this.validFrames,
      validFrameRatio: validRatio,
      missingLandmarkFrames: this.missingFrames,
      outlierFramesCount: this.outlierCount,
      interpolatedFramesCount: this.interpolatedCount,
      landmarkQualityScore: Math.max(0, Math.min(100, avgConfidence)),
      jitterScore: avgJitter,
      movementCompleted,
      completionScore,
      minLeftAngle: minLeft,
      maxLeftAngle: maxLeft,
      minRightAngle: minRight,
      maxRightAngle: maxRight,
      leftRom,
      rightRom,
      leftExcursion,
      rightExcursion,
      requiredExcursion: this.MIN_ROM_COMPLETION_DEG,
      kneeSymmetry: Math.max(30, Math.min(100, kneeSym)),
      framingStatus: framing.framingStatus,
      userGuidance: framing.userGuidance
    };
  }

  /**
   * Returns live diagnostic metrics for real-time diagnostic panel overlay
   */
  public getLiveDiagnostics() {
    const leftExcursion = Math.max(0, this.leftBaselineStandingAngle - this.leftDeepestFlexionAngle);
    const rightExcursion = Math.max(0, this.rightBaselineStandingAngle - this.rightDeepestFlexionAngle);
    return {
      leftBaseline: this.leftBaselineStandingAngle,
      rightBaseline: this.rightBaselineStandingAngle,
      leftDeepest: this.leftDeepestFlexionAngle,
      rightDeepest: this.rightDeepestFlexionAngle,
      leftExcursion,
      rightExcursion,
      requiredExcursion: this.MIN_ROM_COMPLETION_DEG,
      leftReturn: this.leftReturnDetected,
      rightReturn: this.rightReturnDetected,
      validFrames: this.validFrames,
      totalFrames: this.totalFrames
    };
  }
}
