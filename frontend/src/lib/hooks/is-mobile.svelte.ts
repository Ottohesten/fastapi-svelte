import { untrack } from "svelte";
import { browser } from "$app/environment";

const MOBILE_BREAKPOINT = 768;

export class IsMobile {
	#current = $state<boolean>(false);

	constructor() {
		if (!browser) {
			// SSR: leave default false and skip window usage
			return;
		}
		$effect(() => {
			return untrack(() => {
				const mql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`);
				const onChange = () => {
					this.#current = window.innerWidth < MOBILE_BREAKPOINT;
				};
				mql.addEventListener("change", onChange);
				onChange();
				return () => {
					mql.removeEventListener("change", onChange);
				};
			});
		});
	}

	get current() {
		return this.#current;
	}
}
