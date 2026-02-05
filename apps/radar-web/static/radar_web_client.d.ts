/* tslint:disable */
/* eslint-disable */

/**
 * Initialize and run the radar visualization app.
 */
export function main(): Promise<void>;

export type InitInput = RequestInfo | URL | Response | BufferSource | WebAssembly.Module;

export interface InitOutput {
    readonly memory: WebAssembly.Memory;
    readonly main: () => void;
    readonly wasm_bindgen__closure__destroy__h1e3f4ca5aa151a6e: (a: number, b: number) => void;
    readonly wasm_bindgen__closure__destroy__h884ba26e6be82adb: (a: number, b: number) => void;
    readonly wasm_bindgen__closure__destroy__hb43957524d94552c: (a: number, b: number) => void;
    readonly wasm_bindgen__closure__destroy__hd00958357d21c21c: (a: number, b: number) => void;
    readonly wasm_bindgen__closure__destroy__h69352492e3b136ab: (a: number, b: number) => void;
    readonly wasm_bindgen__closure__destroy__h021c1f4cc6689565: (a: number, b: number) => void;
    readonly wasm_bindgen__closure__destroy__h5de276f8148261d0: (a: number, b: number) => void;
    readonly wasm_bindgen__closure__destroy__hd85d1ad578d174df: (a: number, b: number) => void;
    readonly wasm_bindgen__closure__destroy__hb205f5f9f90dccf6: (a: number, b: number) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h0068df046035dd34: (a: number, b: number, c: number) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h97d9841714fac3d9: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__hacf257c58c3e707e: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h6f92f95355a291ae: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h59eb98174ec2e1df: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h069d26f488822cdd: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__hdd8e2a4c6519dcbd: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h630e19bc80c22d01: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h4ce9ffda94ce5582: (a: number, b: number) => number;
    readonly wasm_bindgen__convert__closures_____invoke__h68a9d0a4881893dd: (a: number, b: number) => void;
    readonly __wbindgen_malloc: (a: number, b: number) => number;
    readonly __wbindgen_realloc: (a: number, b: number, c: number, d: number) => number;
    readonly __wbindgen_exn_store: (a: number) => void;
    readonly __externref_table_alloc: () => number;
    readonly __wbindgen_externrefs: WebAssembly.Table;
    readonly __wbindgen_free: (a: number, b: number, c: number) => void;
    readonly __wbindgen_start: () => void;
}

export type SyncInitInput = BufferSource | WebAssembly.Module;

/**
 * Instantiates the given `module`, which can either be bytes or
 * a precompiled `WebAssembly.Module`.
 *
 * @param {{ module: SyncInitInput }} module - Passing `SyncInitInput` directly is deprecated.
 *
 * @returns {InitOutput}
 */
export function initSync(module: { module: SyncInitInput } | SyncInitInput): InitOutput;

/**
 * If `module_or_path` is {RequestInfo} or {URL}, makes a request and
 * for everything else, calls `WebAssembly.instantiate` directly.
 *
 * @param {{ module_or_path: InitInput | Promise<InitInput> }} module_or_path - Passing `InitInput` directly is deprecated.
 *
 * @returns {Promise<InitOutput>}
 */
export default function __wbg_init (module_or_path?: { module_or_path: InitInput | Promise<InitInput> } | InitInput | Promise<InitInput>): Promise<InitOutput>;
