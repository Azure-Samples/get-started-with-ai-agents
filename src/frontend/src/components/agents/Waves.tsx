import type { ReactElement } from 'react';

import { useEffect, useRef } from 'react';

import { useThemeContext } from '../core/theme/ThemeContext';
import { useIsMotionReduced } from './hooks/useIsMotionReduced';

/**
 * Extra parameters for wave movement.
 */
const verticalFreq = 0.02;
const heightScale = 1;
const phase = 0;
const verticalPhase = 0;

/**
 * Default wave layers configuration
 */
const waves = [
  // Front wave - moves fastest and is most prominent
  {
    amplitude: 20,
    frequency: 0.004,
    speed: 0.02,
    colorDark: 'hsla(0, 0%, 40%, 0.2)',
    colorLight: 'hsla(0, 0%, 60%, 0.2)',
    baseHeight: 0.9,
    verticalAmplitude: 8,
    parallaxFactor: 1,
  },
  // Middle wave - moves slower than front wave
  {
    amplitude: 15,
    frequency: 0.007,
    speed: 0.015,
    colorDark: 'hsla(0, 0%, 30%, 0.2)',
    colorLight: 'hsla(0, 0%, 70%, 0.2)',
    baseHeight: 0.71,
    verticalAmplitude: 12,
    parallaxFactor: 0.7,
  },
  // Back wave - moves slowest and is least prominent
  {
    amplitude: 12,
    frequency: 0.01,
    speed: 0.01,
    colorDark: 'hsla(0, 0%, 20%, 0.2)',
    colorLight: 'hsla(0, 0%, 80%, 0.2)',
    baseHeight: 0.6,
    verticalAmplitude: 15,
    parallaxFactor: 0.4,
  },
];

/**
 * Creates an animated wave background using Canvas.
 * Each wave layer can have its own properties for amplitude, speed, and movement.
 */
export function Waves({
  className,
  paused,
}: {
  className?: string;
  paused?: boolean;
}): ReactElement {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number | null>(null);
  const timeRef = useRef<number>(0);
  const lastTimeRef = useRef<number>(performance.now());
  const startTimeRef = useRef<number>(performance.now());

  const { currentTheme } = useThemeContext();

  const isMotionReduced = useIsMotionReduced();

  useEffect(() => {
    const drawWave = (
      ctx: CanvasRenderingContext2D,
      wave: (typeof waves)[number],
      canvasWidth: number,
      canvasHeight: number,
      time: number,
    ) => {
      const {
        amplitude,
        frequency,
        speed,
        colorDark,
        colorLight,
        baseHeight,
        verticalAmplitude,
        parallaxFactor,
      } = wave;

      // Calculate vertical oscillation
      const verticalOffset =
        verticalAmplitude *
        Math.sin(time * verticalFreq * parallaxFactor + verticalPhase);

      // Begin drawing path
      ctx.beginPath();
      ctx.moveTo(0, canvasHeight);

      // Draw wave points
      const steps = Math.ceil(canvasWidth);
      for (let i = 0; i <= steps; i++) {
        const x = (i / steps) * canvasWidth;
        const wavePos = x * frequency + time * speed * parallaxFactor + phase;

        // Calculate wave height with simple sine wave
        const waveHeight = Math.sin(wavePos) * amplitude * heightScale;

        // Calculate final position
        const y =
          canvasHeight * baseHeight +
          verticalOffset * parallaxFactor +
          waveHeight;

        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }

      // Complete the wave path
      ctx.lineTo(canvasWidth, canvasHeight);
      ctx.lineTo(0, canvasHeight);
      ctx.closePath();

      // Fill the wave
      ctx.fillStyle = currentTheme === 'Dark' ? colorDark : colorLight;
      ctx.fill();
    };

    const animate = () => {
      const canvas = canvasRef.current;
      if (!canvas) {
        return;
      }

      const ctx = canvas.getContext('2d', { alpha: true });
      if (!ctx) {
        return;
      }

      // Calculate elapsed time since animation started
      const currentTime = performance.now();

      // Calculate smooth delta time
      const deltaTime = (currentTime - lastTimeRef.current) / 1000;
      lastTimeRef.current = currentTime;

      // Update animation time
      timeRef.current += deltaTime * 50;

      // Clear canvas completely
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw all waves from back to front
      const reversedWaves = [...waves].reverse();
      for (const wave of reversedWaves) {
        drawWave(ctx, wave, canvas.width, canvas.height, timeRef.current);
      }

      if (!isMotionReduced && !paused) {
        animationRef.current = requestAnimationFrame(animate);
      }
    };

    const handleResize = () => {
      const canvas = canvasRef.current;
      if (!canvas) {
        return;
      }

      const rect = canvas.parentElement?.getBoundingClientRect();
      if (rect) {
        canvas.width = rect.width;
        canvas.height = rect.height;
      }

      animate();
    };

    // Reset the start time reference when the component mounts
    startTimeRef.current = performance.now();

    // Initialize animation and resize handler
    handleResize();

    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      if (animationRef.current != null) {
        cancelAnimationFrame(animationRef.current);
      }
      window.removeEventListener('resize', handleResize);
    };
  }, [isMotionReduced, paused, currentTheme]);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden={true}
      className={className}
      data-testid="waves-animation"
    />
  );
}
