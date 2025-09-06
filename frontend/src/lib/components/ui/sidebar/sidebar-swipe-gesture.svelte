<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { useSidebar } from './context.svelte.js';

	const sidebar = useSidebar();

	let startX = 0;
	let startY = 0;
	let trackingOpen = false;
	let trackingClose = false;

	const EDGE_PX = 200; // Only start swipe from the very left edge
	const SWIPE_THRESHOLD = 50; // Min horizontal distance to trigger
	const HORIZ_BIAS = 1.5; // Require horizontal movement > vertical * bias

	function onTouchStart(e: TouchEvent) {
		if (!sidebar.isMobile) return;
		if (e.touches.length !== 1) return;
		const t = e.touches[0];
		if (sidebar.openMobile) {
			// Sidebar is open: enable swipe-left-to-close from anywhere
			startX = t.clientX;
			startY = t.clientY;
			trackingClose = true;
			trackingOpen = false;
			return;
		}
		// Sidebar closed: only start open-tracking from left edge
		if (t.clientX > EDGE_PX) return;
		startX = t.clientX;
		startY = t.clientY;
		trackingOpen = true;
		trackingClose = false;
	}

	function onTouchMove(e: TouchEvent) {
		if (!trackingOpen && !trackingClose) return;
		const t = e.touches[0];
		const dx = t.clientX - startX;
		const dy = Math.abs(t.clientY - startY);

		if (trackingOpen) {
			// If horizontal movement dominates and exceeds threshold, open sidebar
			if (dx > SWIPE_THRESHOLD && dx > dy * HORIZ_BIAS) {
				sidebar.setOpenMobile(true);
				trackingOpen = false;
				trackingClose = false;
				return;
			}
			// Cancel if the gesture reverses direction
			if (dx < -10) trackingOpen = false;
		}

		if (trackingClose) {
			// Swipe left to close when open
			if (dx < -SWIPE_THRESHOLD && Math.abs(dx) > dy * HORIZ_BIAS) {
				sidebar.setOpenMobile(false);
				trackingClose = false;
				trackingOpen = false;
				return;
			}
			// Cancel if moving right instead
			if (dx > 10) trackingClose = false;
		}
	}

	function onTouchEnd() {
		trackingOpen = false;
		trackingClose = false;
	}

	onMount(() => {
		if (typeof window === 'undefined') return;
		window.addEventListener('touchstart', onTouchStart, { passive: true });
		window.addEventListener('touchmove', onTouchMove, { passive: true });
		window.addEventListener('touchend', onTouchEnd, { passive: true });
	});

	onDestroy(() => {
		if (typeof window === 'undefined') return;
		window.removeEventListener('touchstart', onTouchStart as any);
		window.removeEventListener('touchmove', onTouchMove as any);
		window.removeEventListener('touchend', onTouchEnd as any);
	});
</script>

<!-- No visible UI; this component only attaches global touch handlers on mobile -->
