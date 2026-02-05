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
    readonly wasm_bindgen__closure__destroy__ha157ccf0ab72b46c: (a: number, b: number) => void;
    readonly wasm_bindgen__closure__destroy__he41d28c1907a046e: (a: number, b: number) => void;
    readonly wasm_bindgen__closure__destroy__hb205f5f9f90dccf6: (a: number, b: number) => void;
    readonly wasm_bindgen__closure__destroy__he58f27e7277a0bce: (a: number, b: number) => void;
    readonly wasm_bindgen__closure__destroy__h4a728242c61dcfa9: (a: number, b: number) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h9e0a4c62f8bc48d7: (a: number, b: number, c: number) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h666172b7eeeeb412: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h630e19bc80c22d01: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h850daf4f85c35d83: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__he0158893042d4229: (a: number, b: number, c: any) => void;
    readonly wasm_bindgen__convert__closures_____invoke__h4ce9ffda94ce5582: (a: number, b: number) => number;
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
