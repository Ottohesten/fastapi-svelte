import { browser } from "$app/environment";
import { pushState } from "$app/navigation";
import { page } from "$app/state";

type ShallowOverlayOptions = {
    id: string;
    getOpen: () => boolean;
    setOpen: (open: boolean) => void;
    getEnabled: () => boolean;
};

function getOverlayStack(): string[] {
    return page.state.shallowOverlays ?? [];
}

export function useShallowOverlay(options: ShallowOverlayOptions) {
    const id = options.id;
    let initialized = false;
    let lastOpen = options.getOpen();
    let lastActive = false;
    let lastEnabled = options.getEnabled();
    let popPending = false;

    function updateOpen(open: boolean) {
        lastOpen = open;
        if (options.getOpen() !== open) options.setOpen(open);
    }

    function pushOverlay() {
        const stack = getOverlayStack();
        if (stack.includes(id)) return;

        popPending = false;
        pushState("", {
            ...page.state,
            shallowOverlays: [...stack, id]
        });
    }

    function popOverlay() {
        if (popPending) return;

        const stack = getOverlayStack();
        const index = stack.lastIndexOf(id);

        if (index === -1) {
            updateOpen(false);
            return;
        }

        popPending = true;

        // If this overlay has another overlay above it, close the complete nested stack.
        const steps = stack.length - index;
        if (steps === 1) history.back();
        else history.go(-steps);
    }

    $effect(() => {
        if (!browser) return;

        const enabled = options.getEnabled();
        const open = options.getOpen();
        const active = getOverlayStack().includes(id);

        if (!initialized) {
            initialized = true;
            lastOpen = open;
            lastActive = active;
            lastEnabled = enabled;

            if (!enabled) return;
            if (active) updateOpen(true);
            else if (open) pushOverlay();
            return;
        }

        if (enabled !== lastEnabled) {
            lastEnabled = enabled;
            lastOpen = open;
            lastActive = active;

            if (enabled) {
                if (active) updateOpen(true);
                else if (open) pushOverlay();
            }
            return;
        }

        if (!enabled) {
            lastOpen = open;
            lastActive = active;
            return;
        }

        // Back and forward update page.state without running navigation hooks.
        if (active !== lastActive) {
            lastActive = active;
            popPending = false;
            updateOpen(active);
            return;
        }

        // Also support parents that change a bound `open` value programmatically.
        if (open !== lastOpen) {
            lastOpen = open;
            if (open) pushOverlay();
            else popOverlay();
        }
    });

    return {
        handleOpenChange(open: boolean) {
            if (!options.getEnabled()) {
                updateOpen(open);
                return;
            }

            if (open) {
                updateOpen(true);
                pushOverlay();
            } else {
                popOverlay();
            }
        }
    };
}
