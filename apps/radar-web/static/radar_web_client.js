/* @ts-self-types="./radar_web_client.d.ts" */

//#region exports

/**
 * Initialize and run the radar visualization app.
 * @returns {Promise<void>}
 */
export function main() {
    wasm.main();
}

//#endregion

//#region wasm imports

function __wbg_get_imports() {
    const import0 = {
        __proto__: null,
        __wbg_Window_9e7ea8667e28eb00: function() { return logError(function (arg0) {
            const ret = arg0.Window;
            return ret;
        }, arguments); },
        __wbg_WorkerGlobalScope_0169ffb9adb5f5ef: function() { return logError(function (arg0) {
            const ret = arg0.WorkerGlobalScope;
            return ret;
        }, arguments); },
        __wbg___wbindgen_debug_string_0bc8482c6e3508ae: function(arg0, arg1) {
            const ret = debugString(arg1);
            const ptr1 = passStringToWasm0(ret, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
            const len1 = WASM_VECTOR_LEN;
            getDataViewMemory0().setInt32(arg0 + 4 * 1, len1, true);
            getDataViewMemory0().setInt32(arg0 + 4 * 0, ptr1, true);
        },
        __wbg___wbindgen_is_function_0095a73b8b156f76: function(arg0) {
            const ret = typeof(arg0) === 'function';
            _assertBoolean(ret);
            return ret;
        },
        __wbg___wbindgen_is_null_ac34f5003991759a: function(arg0) {
            const ret = arg0 === null;
            _assertBoolean(ret);
            return ret;
        },
        __wbg___wbindgen_is_object_5ae8e5880f2c1fbd: function(arg0) {
            const val = arg0;
            const ret = typeof(val) === 'object' && val !== null;
            _assertBoolean(ret);
            return ret;
        },
        __wbg___wbindgen_is_undefined_9e4d92534c42d778: function(arg0) {
            const ret = arg0 === undefined;
            _assertBoolean(ret);
            return ret;
        },
        __wbg___wbindgen_rethrow_05525c567f154472: function(arg0) {
            throw arg0;
        },
        __wbg___wbindgen_string_get_72fb696202c56729: function(arg0, arg1) {
            const obj = arg1;
            const ret = typeof(obj) === 'string' ? obj : undefined;
            var ptr1 = isLikeNone(ret) ? 0 : passStringToWasm0(ret, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
            var len1 = WASM_VECTOR_LEN;
            getDataViewMemory0().setInt32(arg0 + 4 * 1, len1, true);
            getDataViewMemory0().setInt32(arg0 + 4 * 0, ptr1, true);
        },
        __wbg___wbindgen_throw_be289d5034ed271b: function(arg0, arg1) {
            throw new Error(getStringFromWasm0(arg0, arg1));
        },
        __wbg__wbg_cb_unref_d9b87ff7982e3b21: function() { return logError(function (arg0) {
            arg0._wbg_cb_unref();
        }, arguments); },
        __wbg_add_5be83378df680c25: function() { return handleError(function (arg0, arg1, arg2) {
            arg0.add(getStringFromWasm0(arg1, arg2));
        }, arguments); },
        __wbg_beginComputePass_01f3206a4680f256: function() { return logError(function (arg0, arg1) {
            const ret = arg0.beginComputePass(arg1);
            return ret;
        }, arguments); },
        __wbg_beginRenderPass_aefd0d9681a1f010: function() { return handleError(function (arg0, arg1) {
            const ret = arg0.beginRenderPass(arg1);
            return ret;
        }, arguments); },
        __wbg_buffer_26d0910f3a5bc899: function() { return logError(function (arg0) {
            const ret = arg0.buffer;
            return ret;
        }, arguments); },
        __wbg_call_389efe28435a9388: function() { return handleError(function (arg0, arg1) {
            const ret = arg0.call(arg1);
            return ret;
        }, arguments); },
        __wbg_classList_1a87c34c6d81421e: function() { return logError(function (arg0) {
            const ret = arg0.classList;
            return ret;
        }, arguments); },
        __wbg_clearBuffer_31e63ae370e920a3: function() { return logError(function (arg0, arg1, arg2, arg3) {
            arg0.clearBuffer(arg1, arg2, arg3);
        }, arguments); },
        __wbg_clearBuffer_f0f82b792cfe1f18: function() { return logError(function (arg0, arg1, arg2) {
            arg0.clearBuffer(arg1, arg2);
        }, arguments); },
        __wbg_close_1d08eaf57ed325c0: function() { return handleError(function (arg0) {
            arg0.close();
        }, arguments); },
        __wbg_configure_86dd92dde48d105a: function() { return handleError(function (arg0, arg1) {
            arg0.configure(arg1);
        }, arguments); },
        __wbg_copyBufferToBuffer_0d141e7111b0b6ab: function() { return handleError(function (arg0, arg1, arg2, arg3, arg4, arg5) {
            arg0.copyBufferToBuffer(arg1, arg2, arg3, arg4, arg5);
        }, arguments); },
        __wbg_copyBufferToTexture_722a7aa47b5d891b: function() { return handleError(function (arg0, arg1, arg2, arg3) {
            arg0.copyBufferToTexture(arg1, arg2, arg3);
        }, arguments); },
        __wbg_copyExternalImageToTexture_a2037621913ee52d: function() { return handleError(function (arg0, arg1, arg2, arg3) {
            arg0.copyExternalImageToTexture(arg1, arg2, arg3);
        }, arguments); },
        __wbg_copyTextureToBuffer_bb350c95b19e5999: function() { return handleError(function (arg0, arg1, arg2, arg3) {
            arg0.copyTextureToBuffer(arg1, arg2, arg3);
        }, arguments); },
        __wbg_copyTextureToTexture_e56f4277214ec1b4: function() { return handleError(function (arg0, arg1, arg2, arg3) {
            arg0.copyTextureToTexture(arg1, arg2, arg3);
        }, arguments); },
        __wbg_createBindGroupLayout_f0635625a1a82bea: function() { return handleError(function (arg0, arg1) {
            const ret = arg0.createBindGroupLayout(arg1);
            return ret;
        }, arguments); },
        __wbg_createBindGroup_043b06d20124f91e: function() { return logError(function (arg0, arg1) {
            const ret = arg0.createBindGroup(arg1);
            return ret;
        }, arguments); },
        __wbg_createBuffer_086a8bb05ced884a: function() { return handleError(function (arg0, arg1) {
            const ret = arg0.createBuffer(arg1);
            return ret;
        }, arguments); },
        __wbg_createCommandEncoder_aa9ae9d445bb7abf: function() { return logError(function (arg0, arg1) {
            const ret = arg0.createCommandEncoder(arg1);
            return ret;
        }, arguments); },
        __wbg_createComputePipeline_059cf7af9b47a3fc: function() { return logError(function (arg0, arg1) {
            const ret = arg0.createComputePipeline(arg1);
            return ret;
        }, arguments); },
        __wbg_createPipelineLayout_5cc7e994e46201c7: function() { return logError(function (arg0, arg1) {
            const ret = arg0.createPipelineLayout(arg1);
            return ret;
        }, arguments); },
        __wbg_createQuerySet_0eb86b1d17c9df17: function() { return handleError(function (arg0, arg1) {
            const ret = arg0.createQuerySet(arg1);
            return ret;
        }, arguments); },
        __wbg_createRenderBundleEncoder_95f5b5446f199cbd: function() { return handleError(function (arg0, arg1) {
            const ret = arg0.createRenderBundleEncoder(arg1);
            return ret;
        }, arguments); },
        __wbg_createRenderPipeline_47152f2f57b11194: function() { return handleError(function (arg0, arg1) {
            const ret = arg0.createRenderPipeline(arg1);
            return ret;
        }, arguments); },
        __wbg_createSampler_f3970b77a6f36963: function() { return logError(function (arg0, arg1) {
            const ret = arg0.createSampler(arg1);
            return ret;
        }, arguments); },
        __wbg_createShaderModule_9ec201507fe4949e: function() { return logError(function (arg0, arg1) {
            const ret = arg0.createShaderModule(arg1);
            return ret;
        }, arguments); },
        __wbg_createTask_deeb88a68fc97c9d: function() { return handleError(function (arg0, arg1) {
            const ret = console.createTask(getStringFromWasm0(arg0, arg1));
            return ret;
        }, arguments); },
        __wbg_createTexture_09f18232c5ad6e69: function() { return handleError(function (arg0, arg1) {
            const ret = arg0.createTexture(arg1);
            return ret;
        }, arguments); },
        __wbg_createView_f7cd0a0356a46f3b: function() { return handleError(function (arg0, arg1) {
            const ret = arg0.createView(arg1);
            return ret;
        }, arguments); },
        __wbg_data_5330da50312d0bc1: function() { return logError(function (arg0) {
            const ret = arg0.data;
            return ret;
        }, arguments); },
        __wbg_debug_a4099fa12db6cd61: function() { return logError(function (arg0) {
            console.debug(arg0);
        }, arguments); },
        __wbg_destroy_0252d01ac8a09285: function() { return logError(function (arg0) {
            arg0.destroy();
        }, arguments); },
        __wbg_destroy_9ec012febca0b2bc: function() { return logError(function (arg0) {
            arg0.destroy();
        }, arguments); },
        __wbg_destroy_c8cba128dc1a0e2d: function() { return logError(function (arg0) {
            arg0.destroy();
        }, arguments); },
        __wbg_document_ee35a3d3ae34ef6c: function() { return logError(function (arg0) {
            const ret = arg0.document;
            return isLikeNone(ret) ? 0 : addToExternrefTable0(ret);
        }, arguments); },
        __wbg_done_57b39ecd9addfe81: function() { return logError(function (arg0) {
            const ret = arg0.done;
            _assertBoolean(ret);
            return ret;
        }, arguments); },
        __wbg_drawIndexedIndirect_90027e802dbb47e6: function() { return logError(function (arg0, arg1, arg2) {
            arg0.drawIndexedIndirect(arg1, arg2);
        }, arguments); },
        __wbg_drawIndexed_322c2f9f038d7b23: function() { return logError(function (arg0, arg1, arg2, arg3, arg4, arg5) {
            arg0.drawIndexed(arg1 >>> 0, arg2 >>> 0, arg3 >>> 0, arg4, arg5 >>> 0);
        }, arguments); },
        __wbg_drawIndirect_0794414da8ea662e: function() { return logError(function (arg0, arg1, arg2) {
            arg0.drawIndirect(arg1, arg2);
        }, arguments); },
        __wbg_draw_d38c9207eb049f56: function() { return logError(function (arg0, arg1, arg2, arg3, arg4) {
            arg0.draw(arg1 >>> 0, arg2 >>> 0, arg3 >>> 0, arg4 >>> 0);
        }, arguments); },
        __wbg_end_d54348baf0bf3b70: function() { return logError(function (arg0) {
            arg0.end();
        }, arguments); },
        __wbg_error_53172b72ea901998: function() { return logError(function (arg0) {
            const ret = arg0.error;
            return ret;
        }, arguments); },
        __wbg_error_7534b8e9a36f1ab4: function() { return logError(function (arg0, arg1) {
            let deferred0_0;
            let deferred0_1;
            try {
                deferred0_0 = arg0;
                deferred0_1 = arg1;
                console.error(getStringFromWasm0(arg0, arg1));
            } finally {
                wasm.__wbindgen_free(deferred0_0, deferred0_1, 1);
            }
        }, arguments); },
        __wbg_error_9a7fe3f932034cde: function() { return logError(function (arg0) {
            console.error(arg0);
        }, arguments); },
        __wbg_executeBundles_22ae3b0de1d09e91: function() { return logError(function (arg0, arg1) {
            arg0.executeBundles(arg1);
        }, arguments); },
        __wbg_features_689574262f9403d5: function() { return logError(function (arg0) {
            const ret = arg0.features;
            return ret;
        }, arguments); },
        __wbg_features_a4866072bcfdb3fb: function() { return logError(function (arg0) {
            const ret = arg0.features;
            return ret;
        }, arguments); },
        __wbg_finish_db34a19c90c07af7: function() { return logError(function (arg0) {
            const ret = arg0.finish();
            return ret;
        }, arguments); },
        __wbg_finish_e2d3808af76b422a: function() { return logError(function (arg0, arg1) {
            const ret = arg0.finish(arg1);
            return ret;
        }, arguments); },
        __wbg_getBoundingClientRect_b5c8c34d07878818: function() { return logError(function (arg0) {
            const ret = arg0.getBoundingClientRect();
            return ret;
        }, arguments); },
        __wbg_getContext_2966500392030d63: function() { return handleError(function (arg0, arg1, arg2) {
            const ret = arg0.getContext(getStringFromWasm0(arg1, arg2));
            return isLikeNone(ret) ? 0 : addToExternrefTable0(ret);
        }, arguments); },
        __wbg_getContext_2a5764d48600bc43: function() { return handleError(function (arg0, arg1, arg2) {
            const ret = arg0.getContext(getStringFromWasm0(arg1, arg2));
            return isLikeNone(ret) ? 0 : addToExternrefTable0(ret);
        }, arguments); },
        __wbg_getCurrentTexture_6ee19b05d6ba43ba: function() { return handleError(function (arg0) {
            const ret = arg0.getCurrentTexture();
            return ret;
        }, arguments); },
        __wbg_getElementById_e34377b79d7285f6: function() { return logError(function (arg0, arg1, arg2) {
            const ret = arg0.getElementById(getStringFromWasm0(arg1, arg2));
            return isLikeNone(ret) ? 0 : addToExternrefTable0(ret);
        }, arguments); },
        __wbg_getMappedRange_b986a889b6b53379: function() { return handleError(function (arg0, arg1, arg2) {
            const ret = arg0.getMappedRange(arg1, arg2);
            return ret;
        }, arguments); },
        __wbg_getPreferredCanvasFormat_c56b5a9a243fe942: function() { return logError(function (arg0) {
            const ret = arg0.getPreferredCanvasFormat();
            return (__wbindgen_enum_GpuTextureFormat.indexOf(ret) + 1 || 96) - 1;
        }, arguments); },
        __wbg_get_d8db2ad31d529ff8: function() { return logError(function (arg0, arg1) {
            const ret = arg0[arg1 >>> 0];
            return isLikeNone(ret) ? 0 : addToExternrefTable0(ret);
        }, arguments); },
        __wbg_gpu_1b22165b67dd5a59: function() { return logError(function (arg0) {
            const ret = arg0.gpu;
            return ret;
        }, arguments); },
        __wbg_has_c563a404388202f5: function() { return logError(function (arg0, arg1, arg2) {
            const ret = arg0.has(getStringFromWasm0(arg1, arg2));
            _assertBoolean(ret);
            return ret;
        }, arguments); },
        __wbg_height_38750dc6de41ee75: function() { return logError(function (arg0) {
            const ret = arg0.height;
            _assertNum(ret);
            return ret;
        }, arguments); },
        __wbg_height_45209601b4c4ede6: function() { return logError(function (arg0) {
            const ret = arg0.height;
            return ret;
        }, arguments); },
        __wbg_host_92d607209031b72c: function() { return handleError(function (arg0, arg1) {
            const ret = arg1.host;
            const ptr1 = passStringToWasm0(ret, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
            const len1 = WASM_VECTOR_LEN;
            getDataViewMemory0().setInt32(arg0 + 4 * 1, len1, true);
            getDataViewMemory0().setInt32(arg0 + 4 * 0, ptr1, true);
        }, arguments); },
        __wbg_info_148d043840582012: function() { return logError(function (arg0) {
            console.info(arg0);
        }, arguments); },
        __wbg_instanceof_ArrayBuffer_c367199e2fa2aa04: function() { return logError(function (arg0) {
            let result;
            try {
                result = arg0 instanceof ArrayBuffer;
            } catch (_) {
                result = false;
            }
            const ret = result;
            _assertBoolean(ret);
            return ret;
        }, arguments); },
        __wbg_instanceof_GpuAdapter_331cc7dcda68de8c: function() { return logError(function (arg0) {
            let result;
            try {
                result = arg0 instanceof GPUAdapter;
            } catch (_) {
                result = false;
            }
            const ret = result;
            _assertBoolean(ret);
            return ret;
        }, arguments); },
        __wbg_instanceof_GpuCanvasContext_4ea475a10f693c29: function() { return logError(function (arg0) {
            let result;
            try {
                result = arg0 instanceof GPUCanvasContext;
            } catch (_) {
                result = false;
            }
            const ret = result;
            _assertBoolean(ret);
            return ret;
        }, arguments); },
        __wbg_instanceof_GpuDeviceLostInfo_ad89975227239f55: function() { return logError(function (arg0) {
            let result;
            try {
                result = arg0 instanceof GPUDeviceLostInfo;
            } catch (_) {
                result = false;
            }
            const ret = result;
            _assertBoolean(ret);
            return ret;
        }, arguments); },
        __wbg_instanceof_GpuOutOfMemoryError_37ed19bdb2cf4ac4: function() { return logError(function (arg0) {
            let result;
            try {
                result = arg0 instanceof GPUOutOfMemoryError;
            } catch (_) {
                result = false;
            }
            const ret = result;
            _assertBoolean(ret);
            return ret;
        }, arguments); },
        __wbg_instanceof_GpuValidationError_6dca0186e4a231ce: function() { return logError(function (arg0) {
            let result;
            try {
                result = arg0 instanceof GPUValidationError;
            } catch (_) {
                result = false;
            }
            const ret = result;
            _assertBoolean(ret);
            return ret;
        }, arguments); },
        __wbg_instanceof_HtmlCanvasElement_3f2f6e1edb1c9792: function() { return logError(function (arg0) {
            let result;
            try {
                result = arg0 instanceof HTMLCanvasElement;
            } catch (_) {
                result = false;
            }
            const ret = result;
            _assertBoolean(ret);
            return ret;
        }, arguments); },
        __wbg_instanceof_Object_1c6af87502b733ed: function() { return logError(function (arg0) {
            let result;
            try {
                result = arg0 instanceof Object;
            } catch (_) {
                result = false;
            }
            const ret = result;
            _assertBoolean(ret);
            return ret;
        }, arguments); },
        __wbg_instanceof_Window_ed49b2db8df90359: function() { return logError(function (arg0) {
            let result;
            try {
                result = arg0 instanceof Window;
            } catch (_) {
                result = false;
            }
            const ret = result;
            _assertBoolean(ret);
            return ret;
        }, arguments); },
        __wbg_keys_f7c3c12857423fd2: function() { return logError(function (arg0) {
            const ret = arg0.keys();
            return ret;
        }, arguments); },
        __wbg_label_7045a786095b1bab: function() { return logError(function (arg0, arg1) {
            const ret = arg1.label;
            const ptr1 = passStringToWasm0(ret, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
            const len1 = WASM_VECTOR_LEN;
            getDataViewMemory0().setInt32(arg0 + 4 * 1, len1, true);
            getDataViewMemory0().setInt32(arg0 + 4 * 0, ptr1, true);
        }, arguments); },
        __wbg_length_32ed9a279acd054c: function() { return logError(function (arg0) {
            const ret = arg0.length;
            _assertNum(ret);
            return ret;
        }, arguments); },
        __wbg_limits_563f98195b4aab75: function() { return logError(function (arg0) {
            const ret = arg0.limits;
            return ret;
        }, arguments); },
        __wbg_limits_6e5836ab03ee64b4: function() { return logError(function (arg0) {
            const ret = arg0.limits;
            return ret;
        }, arguments); },
        __wbg_location_df7ca06c93e51763: function() { return logError(function (arg0) {
            const ret = arg0.location;
            return ret;
        }, arguments); },
        __wbg_log_6b5ca2e6124b2808: function() { return logError(function (arg0) {
            console.log(arg0);
        }, arguments); },
        __wbg_lost_f5ec8721e4b1cbd0: function() { return logError(function (arg0) {
            const ret = arg0.lost;
            return ret;
        }, arguments); },
        __wbg_mapAsync_61fd3c4dd9f60c6d: function() { return logError(function (arg0, arg1, arg2, arg3) {
            const ret = arg0.mapAsync(arg1 >>> 0, arg2, arg3);
            return ret;
        }, arguments); },
        __wbg_maxBindGroups_30d01da76ad53580: function() { return logError(function (arg0) {
            const ret = arg0.maxBindGroups;
            _assertNum(ret);
            return ret;
        }, arguments); },
        __wbg_maxBindingsPerBindGroup_3dcdeb4a7de67a4a: function() { return logError(function (arg0) {
            const ret = arg0.maxBindingsPerBindGroup;
            _assertNum(ret);
            return ret;
        }, arguments); },
        __wbg_maxBufferSize_a3c3e79851bb49a7: function() { return logError(function (arg0) {
            const ret = arg0.maxBufferSize;
            return ret;
        }, arguments); },
        __wbg_maxColorAttachmentBytesPerSample_61daf47ae1b88dc2: function() { return logError(function (arg0) {
            const ret = arg0.maxColorAttachmentBytesPerSample;
            _assertNum(ret);
            return ret;
        }, arguments); },
        __wbg_maxColorAttachments_f8f65390ed7c3dcd: function() { return logError(function (arg0) {
            const ret = arg0.maxColorAttachments;
            _assertNum(ret);
            return ret;
        }, arguments); },
        __wbg_maxComputeInvocationsPerWorkgroup_dbfa932a2c3d9ca0: function() { return logError(function (arg0) {
            const ret = arg0.maxComputeInvocationsPerWorkgroup;
            _assertNum(ret);
            return ret;
        }, arguments); },
        __wbg_maxComputeWorkgroupSizeX_2a7fdde2d850eb69: function() { return logError(function (arg0) {
            const ret = arg0.maxComputeWorkgroupSizeX;
            _assertNum(ret);
            return ret;
        }, arguments); },
        __wbg_maxComputeWorkgroupSizeY_ae6eb3af592e045d: function() { return logError(function (arg0) {
            const ret = arg0.maxComputeWorkgroupSizeY;
            _assertNum(ret);
            return ret;
        }, arguments); },
        __wbg_maxComputeWorkgroupSizeZ_df6389c6ad61aa20: function() { return logError(function (arg0) {
            const ret = arg0.maxComputeWorkgroupSizeZ;
            _assertNum(ret);
            return ret;
        }, arguments); },
        __wbg_maxComputeWorkgroupStorageSize_d090d78935189091: function() { return logError(function (arg0) {
            const ret = arg0.maxComputeWorkgroupStorageSize;
            _assertNum(ret);
            return ret;
        }, arguments); },
        __wbg_maxComputeWorkgroupsPerDimension_5d5d832c21854769: function() { return logError(function (arg0) {
            const ret = arg0.maxComputeWorkgroupsPerDimension;
            _assertNum(ret);
            return ret;
        }, arguments); },
        __wbg_maxDynamicStorageBuffersPerPipelineLayout_0d5102fd812fe086: function() { return logError(function (arg0) {
            const ret = arg0.maxDynamicStorageBuffersPerPipelineLayout;
            _assertNum(ret);
            return ret;
        }, arguments); },
        __wbg_maxDynamicUniformBuffersPerPipelineLayout_fd6efab6fa18099a: function() { return logError(function (arg0) {
            const ret = arg0.maxDynamicUniformBuffersPerPipelineLayout;
            _assertNum(ret);
            return ret;
        }, arguments); },
        __wbg_maxSampledTexturesPerShaderStage_4ffa7a7339d366d7: function() { return logError(function (arg0) {
            const ret = arg0.maxSampledTexturesPerShaderStage;
            _assertNum(ret);
            return ret;
        }, arguments); },
        __wbg_maxSamplersPerShaderStage_776dbf5a1fdc58b1: function() { return logError(function (arg0) {
            const ret = arg0.maxSamplersPerShaderStage;
            _assertNum(ret);
            return ret;
        }, arguments); },
        __wbg_maxStorageBufferBindingSize_4a81009504bfcacd: function() { return logError(function (arg0) {
            const ret = arg0.maxStorageBufferBindingSize;
            return ret;
        }, arguments); },
        __wbg_maxStorageBuffersPerShaderStage_772149c39281f13c: function() { return logError(function (arg0) {
            const ret = arg0.maxStorageBuffersPerShaderStage;
            _assertNum(ret);
            return ret;
        }, arguments); },
        __wbg_maxStorageTexturesPerShaderStage_181856fa7bd31bd2: function() { return logError(function (arg0) {
            const ret = arg0.maxStorageTexturesPerShaderStage;
            _assertNum(ret);
            return ret;
        }, arguments); },
        __wbg_maxTextureArrayLayers_c50110b7591a08e7: function() { return logError(function (arg0) {
            const ret = arg0.maxTextureArrayLayers;
            _assertNum(ret);
            return ret;
        }, arguments); },
        __wbg_maxTextureDimension1D_8886fff72f64818a: function() { return logError(function (arg0) {
            const ret = arg0.maxTextureDimension1D;
            _assertNum(ret);
            return ret;
        }, arguments); },
        __wbg_maxTextureDimension2D_0e30b1b618696302: function() { return logError(function (arg0) {
            const ret = arg0.maxTextureDimension2D;
            _assertNum(ret);
            return ret;
        }, arguments); },
        __wbg_maxTextureDimension3D_2f567b561a18a953: function() { return logError(function (arg0) {
            const ret = arg0.maxTextureDimension3D;
            _assertNum(ret);
            return ret;
        }, arguments); },
        __wbg_maxUniformBufferBindingSize_50a7723e932bbd63: function() { return logError(function (arg0) {
            const ret = arg0.maxUniformBufferBindingSize;
            return ret;
        }, arguments); },
        __wbg_maxUniformBuffersPerShaderStage_cfac0560ee2b33a2: function() { return logError(function (arg0) {
            const ret = arg0.maxUniformBuffersPerShaderStage;
            _assertNum(ret);
            return ret;
        }, arguments); },
        __wbg_maxVertexAttributes_6bd060b2025920cc: function() { return logError(function (arg0) {
            const ret = arg0.maxVertexAttributes;
            _assertNum(ret);
            return ret;
        }, arguments); },
        __wbg_maxVertexBufferArrayStride_b3c77c1ff836be9f: function() { return logError(function (arg0) {
            const ret = arg0.maxVertexBufferArrayStride;
            _assertNum(ret);
            return ret;
        }, arguments); },
        __wbg_maxVertexBuffers_b4635256105b2915: function() { return logError(function (arg0) {
            const ret = arg0.maxVertexBuffers;
            _assertNum(ret);
            return ret;
        }, arguments); },
        __wbg_message_49299ab153a3b589: function() { return logError(function (arg0, arg1) {
            const ret = arg1.message;
            const ptr1 = passStringToWasm0(ret, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
            const len1 = WASM_VECTOR_LEN;
            getDataViewMemory0().setInt32(arg0 + 4 * 1, len1, true);
            getDataViewMemory0().setInt32(arg0 + 4 * 0, ptr1, true);
        }, arguments); },
        __wbg_message_db8d05fa07b079c1: function() { return logError(function (arg0, arg1) {
            const ret = arg1.message;
            const ptr1 = passStringToWasm0(ret, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
            const len1 = WASM_VECTOR_LEN;
            getDataViewMemory0().setInt32(arg0 + 4 * 1, len1, true);
            getDataViewMemory0().setInt32(arg0 + 4 * 0, ptr1, true);
        }, arguments); },
        __wbg_minStorageBufferOffsetAlignment_989812b5a6a4b5e7: function() { return logError(function (arg0) {
            const ret = arg0.minStorageBufferOffsetAlignment;
            _assertNum(ret);
            return ret;
        }, arguments); },
        __wbg_minUniformBufferOffsetAlignment_ff7899c34a8303e7: function() { return logError(function (arg0) {
            const ret = arg0.minUniformBufferOffsetAlignment;
            _assertNum(ret);
            return ret;
        }, arguments); },
        __wbg_navigator_43be698ba96fc088: function() { return logError(function (arg0) {
            const ret = arg0.navigator;
            return ret;
        }, arguments); },
        __wbg_navigator_4478931f32ebca57: function() { return logError(function (arg0) {
            const ret = arg0.navigator;
            return ret;
        }, arguments); },
        __wbg_new_057993d5b5e07835: function() { return handleError(function (arg0, arg1) {
            const ret = new WebSocket(getStringFromWasm0(arg0, arg1));
            return ret;
        }, arguments); },
        __wbg_new_361308b2356cecd0: function() { return logError(function () {
            const ret = new Object();
            return ret;
        }, arguments); },
        __wbg_new_3eb36ae241fe6f44: function() { return logError(function () {
            const ret = new Array();
            return ret;
        }, arguments); },
        __wbg_new_8a6f238a6ece86ea: function() { return logError(function () {
            const ret = new Error();
            return ret;
        }, arguments); },
        __wbg_new_dd2b680c8bf6ae29: function() { return logError(function (arg0) {
            const ret = new Uint8Array(arg0);
            return ret;
        }, arguments); },
        __wbg_new_from_slice_a3d2629dc1826784: function() { return logError(function (arg0, arg1) {
            const ret = new Uint8Array(getArrayU8FromWasm0(arg0, arg1));
            return ret;
        }, arguments); },
        __wbg_new_no_args_1c7c842f08d00ebb: function() { return logError(function (arg0, arg1) {
            const ret = new Function(getStringFromWasm0(arg0, arg1));
            return ret;
        }, arguments); },
        __wbg_new_with_byte_offset_and_length_aa261d9c9da49eb1: function() { return logError(function (arg0, arg1, arg2) {
            const ret = new Uint8Array(arg0, arg1 >>> 0, arg2 >>> 0);
            return ret;
        }, arguments); },
        __wbg_next_3482f54c49e8af19: function() { return handleError(function (arg0) {
            const ret = arg0.next();
            return ret;
        }, arguments); },
        __wbg_parentElement_75863410a8617953: function() { return logError(function (arg0) {
            const ret = arg0.parentElement;
            return isLikeNone(ret) ? 0 : addToExternrefTable0(ret);
        }, arguments); },
        __wbg_popErrorScope_4e8ec39111c15bed: function() { return logError(function (arg0) {
            const ret = arg0.popErrorScope();
            return ret;
        }, arguments); },
        __wbg_protocol_4c3b13957de7d079: function() { return handleError(function (arg0, arg1) {
            const ret = arg1.protocol;
            const ptr1 = passStringToWasm0(ret, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
            const len1 = WASM_VECTOR_LEN;
            getDataViewMemory0().setInt32(arg0 + 4 * 1, len1, true);
            getDataViewMemory0().setInt32(arg0 + 4 * 0, ptr1, true);
        }, arguments); },
        __wbg_prototypesetcall_bdcdcc5842e4d77d: function() { return logError(function (arg0, arg1, arg2) {
            Uint8Array.prototype.set.call(getArrayU8FromWasm0(arg0, arg1), arg2);
        }, arguments); },
        __wbg_pushErrorScope_506d26ea9c804e6f: function() { return logError(function (arg0, arg1) {
            arg0.pushErrorScope(__wbindgen_enum_GpuErrorFilter[arg1]);
        }, arguments); },
        __wbg_push_8ffdcb2063340ba5: function() { return logError(function (arg0, arg1) {
            const ret = arg0.push(arg1);
            _assertNum(ret);
            return ret;
        }, arguments); },
        __wbg_querySelectorAll_1283aae52043a951: function() { return handleError(function (arg0, arg1, arg2) {
            const ret = arg0.querySelectorAll(getStringFromWasm0(arg1, arg2));
            return ret;
        }, arguments); },
        __wbg_queueMicrotask_0aa0a927f78f5d98: function() { return logError(function (arg0) {
            const ret = arg0.queueMicrotask;
            return ret;
        }, arguments); },
        __wbg_queueMicrotask_5bb536982f78a56f: function() { return logError(function (arg0) {
            queueMicrotask(arg0);
        }, arguments); },
        __wbg_queue_0ffbb97537a0c4ed: function() { return logError(function (arg0) {
            const ret = arg0.queue;
            return ret;
        }, arguments); },
        __wbg_reason_e0d7cbbd1990668c: function() { return logError(function (arg0) {
            const ret = arg0.reason;
            return (__wbindgen_enum_GpuDeviceLostReason.indexOf(ret) + 1 || 3) - 1;
        }, arguments); },
        __wbg_remove_f9451697e0bc6ca0: function() { return handleError(function (arg0, arg1, arg2) {
            arg0.remove(getStringFromWasm0(arg1, arg2));
        }, arguments); },
        __wbg_requestAdapter_f09d28b3f37de26c: function() { return logError(function (arg0, arg1) {
            const ret = arg0.requestAdapter(arg1);
            return ret;
        }, arguments); },
        __wbg_requestAnimationFrame_43682f8e1c5e5348: function() { return handleError(function (arg0, arg1) {
            const ret = arg0.requestAnimationFrame(arg1);
            _assertNum(ret);
            return ret;
        }, arguments); },
        __wbg_requestDevice_51509dadc50b2e9d: function() { return logError(function (arg0, arg1) {
            const ret = arg0.requestDevice(arg1);
            return ret;
        }, arguments); },
        __wbg_resolveQuerySet_bc4f3482ffb7b68b: function() { return logError(function (arg0, arg1, arg2, arg3, arg4, arg5) {
            arg0.resolveQuerySet(arg1, arg2 >>> 0, arg3 >>> 0, arg4, arg5 >>> 0);
        }, arguments); },
        __wbg_resolve_002c4b7d9d8f6b64: function() { return logError(function (arg0) {
            const ret = Promise.resolve(arg0);
            return ret;
        }, arguments); },
        __wbg_run_bcde7ea43ea6ed7c: function() { return logError(function (arg0, arg1, arg2) {
            try {
                var state0 = {a: arg1, b: arg2};
                var cb0 = () => {
                    const a = state0.a;
                    state0.a = 0;
                    try {
                        return wasm_bindgen__convert__closures_____invoke__h4ce9ffda94ce5582(a, state0.b, );
                    } finally {
                        state0.a = a;
                    }
                };
                const ret = arg0.run(cb0);
                _assertBoolean(ret);
                return ret;
            } finally {
                state0.a = state0.b = 0;
            }
        }, arguments); },
        __wbg_setBindGroup_a81ce7b3934585bf: function() { return logError(function (arg0, arg1, arg2) {
            arg0.setBindGroup(arg1 >>> 0, arg2);
        }, arguments); },
        __wbg_setBindGroup_bb0c2c05b7c49401: function() { return handleError(function (arg0, arg1, arg2, arg3, arg4, arg5, arg6) {
            arg0.setBindGroup(arg1 >>> 0, arg2, getArrayU32FromWasm0(arg3, arg4), arg5, arg6 >>> 0);
        }, arguments); },
        __wbg_setBlendConstant_908030325edd99fe: function() { return handleError(function (arg0, arg1) {
            arg0.setBlendConstant(arg1);
        }, arguments); },
        __wbg_setIndexBuffer_0487a271efcfe0ac: function() { return logError(function (arg0, arg1, arg2, arg3) {
            arg0.setIndexBuffer(arg1, __wbindgen_enum_GpuIndexFormat[arg2], arg3);
        }, arguments); },
        __wbg_setIndexBuffer_97fb24e7cc5b24c0: function() { return logError(function (arg0, arg1, arg2, arg3, arg4) {
            arg0.setIndexBuffer(arg1, __wbindgen_enum_GpuIndexFormat[arg2], arg3, arg4);
        }, arguments); },
        __wbg_setPipeline_78f8f6d440dddd25: function() { return logError(function (arg0, arg1) {
            arg0.setPipeline(arg1);
        }, arguments); },
        __wbg_setScissorRect_4db4ebbc562e249e: function() { return logError(function (arg0, arg1, arg2, arg3, arg4) {
            arg0.setScissorRect(arg1 >>> 0, arg2 >>> 0, arg3 >>> 0, arg4 >>> 0);
        }, arguments); },
        __wbg_setStencilReference_3d2d7ae6284b9f64: function() { return logError(function (arg0, arg1) {
            arg0.setStencilReference(arg1 >>> 0);
        }, arguments); },
        __wbg_setVertexBuffer_b0d3128a04bfd766: function() { return logError(function (arg0, arg1, arg2, arg3, arg4) {
            arg0.setVertexBuffer(arg1 >>> 0, arg2, arg3, arg4);
        }, arguments); },
        __wbg_setVertexBuffer_edbff6ddb5055174: function() { return logError(function (arg0, arg1, arg2, arg3) {
            arg0.setVertexBuffer(arg1 >>> 0, arg2, arg3);
        }, arguments); },
        __wbg_setViewport_b84ead683cd03d3e: function() { return logError(function (arg0, arg1, arg2, arg3, arg4, arg5, arg6) {
            arg0.setViewport(arg1, arg2, arg3, arg4, arg5, arg6);
        }, arguments); },
        __wbg_set_25cf9deff6bf0ea8: function() { return logError(function (arg0, arg1, arg2) {
            arg0.set(arg1, arg2 >>> 0);
        }, arguments); },
        __wbg_set_6cb8631f80447a67: function() { return handleError(function (arg0, arg1, arg2) {
            const ret = Reflect.set(arg0, arg1, arg2);
            _assertBoolean(ret);
            return ret;
        }, arguments); },
        __wbg_set_a_721deab95e136b71: function() { return logError(function (arg0, arg1) {
            arg0.a = arg1;
        }, arguments); },
        __wbg_set_access_b20bfa3ec6b65d05: function() { return logError(function (arg0, arg1) {
            arg0.access = __wbindgen_enum_GpuStorageTextureAccess[arg1];
        }, arguments); },
        __wbg_set_address_mode_u_9c0b2104a94d10f3: function() { return logError(function (arg0, arg1) {
            arg0.addressModeU = __wbindgen_enum_GpuAddressMode[arg1];
        }, arguments); },
        __wbg_set_address_mode_v_a9bedc188ff29608: function() { return logError(function (arg0, arg1) {
            arg0.addressModeV = __wbindgen_enum_GpuAddressMode[arg1];
        }, arguments); },
        __wbg_set_address_mode_w_5774889145ce3789: function() { return logError(function (arg0, arg1) {
            arg0.addressModeW = __wbindgen_enum_GpuAddressMode[arg1];
        }, arguments); },
        __wbg_set_alpha_2c7bdc9da833b6c2: function() { return logError(function (arg0, arg1) {
            arg0.alpha = arg1;
        }, arguments); },
        __wbg_set_alpha_mode_fc3528d234b1fefa: function() { return logError(function (arg0, arg1) {
            arg0.alphaMode = __wbindgen_enum_GpuCanvasAlphaMode[arg1];
        }, arguments); },
        __wbg_set_alpha_to_coverage_enabled_314ce1ca1759b395: function() { return logError(function (arg0, arg1) {
            arg0.alphaToCoverageEnabled = arg1 !== 0;
        }, arguments); },
        __wbg_set_array_layer_count_3c7942d623042874: function() { return logError(function (arg0, arg1) {
            arg0.arrayLayerCount = arg1 >>> 0;
        }, arguments); },
        __wbg_set_array_stride_4b36d0822dea74a8: function() { return logError(function (arg0, arg1) {
            arg0.arrayStride = arg1;
        }, arguments); },
        __wbg_set_aspect_48152f4e4f8231ae: function() { return logError(function (arg0, arg1) {
            arg0.aspect = __wbindgen_enum_GpuTextureAspect[arg1];
        }, arguments); },
        __wbg_set_aspect_f06e234d0aacd1a6: function() { return logError(function (arg0, arg1) {
            arg0.aspect = __wbindgen_enum_GpuTextureAspect[arg1];
        }, arguments); },
        __wbg_set_attributes_382cc084e6792c33: function() { return logError(function (arg0, arg1) {
            arg0.attributes = arg1;
        }, arguments); },
        __wbg_set_b_f53c2f10173c804f: function() { return logError(function (arg0, arg1) {
            arg0.b = arg1;
        }, arguments); },
        __wbg_set_base_array_layer_a5b968338c5c56b6: function() { return logError(function (arg0, arg1) {
            arg0.baseArrayLayer = arg1 >>> 0;
        }, arguments); },
        __wbg_set_base_mip_level_e3288c2d851da708: function() { return logError(function (arg0, arg1) {
            arg0.baseMipLevel = arg1 >>> 0;
        }, arguments); },
        __wbg_set_beginning_of_pass_write_index_35dcbf135e4f9d61: function() { return logError(function (arg0, arg1) {
            arg0.beginningOfPassWriteIndex = arg1 >>> 0;
        }, arguments); },
        __wbg_set_beginning_of_pass_write_index_703995fcd4f84112: function() { return logError(function (arg0, arg1) {
            arg0.beginningOfPassWriteIndex = arg1 >>> 0;
        }, arguments); },
        __wbg_set_binaryType_5bbf62e9f705dc1a: function() { return logError(function (arg0, arg1) {
            arg0.binaryType = __wbindgen_enum_BinaryType[arg1];
        }, arguments); },
        __wbg_set_bind_group_layouts_8de6e109dd34a448: function() { return logError(function (arg0, arg1) {
            arg0.bindGroupLayouts = arg1;
        }, arguments); },
        __wbg_set_binding_5276d6202fceba46: function() { return logError(function (arg0, arg1) {
            arg0.binding = arg1 >>> 0;
        }, arguments); },
        __wbg_set_binding_9e9ed8b6e1418176: function() { return logError(function (arg0, arg1) {
            arg0.binding = arg1 >>> 0;
        }, arguments); },
        __wbg_set_blend_6828ff186670f414: function() { return logError(function (arg0, arg1) {
            arg0.blend = arg1;
        }, arguments); },
        __wbg_set_buffer_1acdac44d9638973: function() { return logError(function (arg0, arg1) {
            arg0.buffer = arg1;
        }, arguments); },
        __wbg_set_buffer_1d16f319d6410e50: function() { return logError(function (arg0, arg1) {
            arg0.buffer = arg1;
        }, arguments); },
        __wbg_set_buffer_74b7b0adf855cf1a: function() { return logError(function (arg0, arg1) {
            arg0.buffer = arg1;
        }, arguments); },
        __wbg_set_buffers_53e83b7c7a5c95aa: function() { return logError(function (arg0, arg1) {
            arg0.buffers = arg1;
        }, arguments); },
        __wbg_set_bytes_per_row_9249690c44f83135: function() { return logError(function (arg0, arg1) {
            arg0.bytesPerRow = arg1 >>> 0;
        }, arguments); },
        __wbg_set_bytes_per_row_ffe6655e20551429: function() { return logError(function (arg0, arg1) {
            arg0.bytesPerRow = arg1 >>> 0;
        }, arguments); },
        __wbg_set_clear_value_f82fff01ed0b5c35: function() { return logError(function (arg0, arg1) {
            arg0.clearValue = arg1;
        }, arguments); },
        __wbg_set_code_6b6ad02fc1705aa2: function() { return logError(function (arg0, arg1, arg2) {
            arg0.code = getStringFromWasm0(arg1, arg2);
        }, arguments); },
        __wbg_set_color_0df2c5f47a951ac1: function() { return logError(function (arg0, arg1) {
            arg0.color = arg1;
        }, arguments); },
        __wbg_set_color_attachments_de625dd9a4850a13: function() { return logError(function (arg0, arg1) {
            arg0.colorAttachments = arg1;
        }, arguments); },
        __wbg_set_color_formats_8619c2e6ee4a59ac: function() { return logError(function (arg0, arg1) {
            arg0.colorFormats = arg1;
        }, arguments); },
        __wbg_set_compare_1b67d8112d05628e: function() { return logError(function (arg0, arg1) {
            arg0.compare = __wbindgen_enum_GpuCompareFunction[arg1];
        }, arguments); },
        __wbg_set_compare_8fbddcdd4781f49a: function() { return logError(function (arg0, arg1) {
            arg0.compare = __wbindgen_enum_GpuCompareFunction[arg1];
        }, arguments); },
        __wbg_set_compute_be8170281283a813: function() { return logError(function (arg0, arg1) {
            arg0.compute = arg1;
        }, arguments); },
        __wbg_set_count_56fa496d577f05ff: function() { return logError(function (arg0, arg1) {
            arg0.count = arg1 >>> 0;
        }, arguments); },
        __wbg_set_count_e8b681b1185cf5da: function() { return logError(function (arg0, arg1) {
            arg0.count = arg1 >>> 0;
        }, arguments); },
        __wbg_set_cull_mode_74bc6eaab528c94b: function() { return logError(function (arg0, arg1) {
            arg0.cullMode = __wbindgen_enum_GpuCullMode[arg1];
        }, arguments); },
        __wbg_set_depth_bias_cdcc35c6971d19cd: function() { return logError(function (arg0, arg1) {
            arg0.depthBias = arg1;
        }, arguments); },
        __wbg_set_depth_bias_clamp_57801e26f66496d9: function() { return logError(function (arg0, arg1) {
            arg0.depthBiasClamp = arg1;
        }, arguments); },
        __wbg_set_depth_bias_slope_scale_81699f807bd5a647: function() { return logError(function (arg0, arg1) {
            arg0.depthBiasSlopeScale = arg1;
        }, arguments); },
        __wbg_set_depth_clear_value_9801aa9eff7645df: function() { return logError(function (arg0, arg1) {
            arg0.depthClearValue = arg1;
        }, arguments); },
        __wbg_set_depth_compare_53d249a136855bd8: function() { return logError(function (arg0, arg1) {
            arg0.depthCompare = __wbindgen_enum_GpuCompareFunction[arg1];
        }, arguments); },
        __wbg_set_depth_fail_op_2e4767995acd4c0a: function() { return logError(function (arg0, arg1) {
            arg0.depthFailOp = __wbindgen_enum_GpuStencilOperation[arg1];
        }, arguments); },
        __wbg_set_depth_load_op_af0b0f05e83f6571: function() { return logError(function (arg0, arg1) {
            arg0.depthLoadOp = __wbindgen_enum_GpuLoadOp[arg1];
        }, arguments); },
        __wbg_set_depth_or_array_layers_5d480fc05509ea0c: function() { return logError(function (arg0, arg1) {
            arg0.depthOrArrayLayers = arg1 >>> 0;
        }, arguments); },
        __wbg_set_depth_read_only_a7b7224074e024d3: function() { return logError(function (arg0, arg1) {
            arg0.depthReadOnly = arg1 !== 0;
        }, arguments); },
        __wbg_set_depth_read_only_c99e728969e6bb74: function() { return logError(function (arg0, arg1) {
            arg0.depthReadOnly = arg1 !== 0;
        }, arguments); },
        __wbg_set_depth_stencil_2bb2fcea55783858: function() { return logError(function (arg0, arg1) {
            arg0.depthStencil = arg1;
        }, arguments); },
        __wbg_set_depth_stencil_attachment_dcbd5b74e4350e16: function() { return logError(function (arg0, arg1) {
            arg0.depthStencilAttachment = arg1;
        }, arguments); },
        __wbg_set_depth_stencil_format_0f8257cabb41cd68: function() { return logError(function (arg0, arg1) {
            arg0.depthStencilFormat = __wbindgen_enum_GpuTextureFormat[arg1];
        }, arguments); },
        __wbg_set_depth_store_op_40dfd99c7e42f894: function() { return logError(function (arg0, arg1) {
            arg0.depthStoreOp = __wbindgen_enum_GpuStoreOp[arg1];
        }, arguments); },
        __wbg_set_depth_write_enabled_4368a2fe5d258cb0: function() { return logError(function (arg0, arg1) {
            arg0.depthWriteEnabled = arg1 !== 0;
        }, arguments); },
        __wbg_set_device_d372d6aa06f20cae: function() { return logError(function (arg0, arg1) {
            arg0.device = arg1;
        }, arguments); },
        __wbg_set_dimension_268b2b7bfc3e2bb8: function() { return logError(function (arg0, arg1) {
            arg0.dimension = __wbindgen_enum_GpuTextureDimension[arg1];
        }, arguments); },
        __wbg_set_dimension_359b229ea1b67a77: function() { return logError(function (arg0, arg1) {
            arg0.dimension = __wbindgen_enum_GpuTextureViewDimension[arg1];
        }, arguments); },
        __wbg_set_dst_factor_96e73b9eaedeb23e: function() { return logError(function (arg0, arg1) {
            arg0.dstFactor = __wbindgen_enum_GpuBlendFactor[arg1];
        }, arguments); },
        __wbg_set_end_of_pass_write_index_71e7659a9d2a9d60: function() { return logError(function (arg0, arg1) {
            arg0.endOfPassWriteIndex = arg1 >>> 0;
        }, arguments); },
        __wbg_set_end_of_pass_write_index_bbe4757d0b985fd3: function() { return logError(function (arg0, arg1) {
            arg0.endOfPassWriteIndex = arg1 >>> 0;
        }, arguments); },
        __wbg_set_entries_5941f16619f54d42: function() { return logError(function (arg0, arg1) {
            arg0.entries = arg1;
        }, arguments); },
        __wbg_set_entries_97a6ad10aa7fa4d1: function() { return logError(function (arg0, arg1) {
            arg0.entries = arg1;
        }, arguments); },
        __wbg_set_entry_point_a858879f63ec2236: function() { return logError(function (arg0, arg1, arg2) {
            arg0.entryPoint = getStringFromWasm0(arg1, arg2);
        }, arguments); },
        __wbg_set_entry_point_a8ce0b22c20548b0: function() { return logError(function (arg0, arg1, arg2) {
            arg0.entryPoint = getStringFromWasm0(arg1, arg2);
        }, arguments); },
        __wbg_set_entry_point_ec35a2279c4d6dd5: function() { return logError(function (arg0, arg1, arg2) {
            arg0.entryPoint = getStringFromWasm0(arg1, arg2);
        }, arguments); },
        __wbg_set_fail_op_d55bda42958efa98: function() { return logError(function (arg0, arg1) {
            arg0.failOp = __wbindgen_enum_GpuStencilOperation[arg1];
        }, arguments); },
        __wbg_set_flip_y_bd2d5ada3a89715f: function() { return logError(function (arg0, arg1) {
            arg0.flipY = arg1 !== 0;
        }, arguments); },
        __wbg_set_format_69ba449c0e080708: function() { return logError(function (arg0, arg1) {
            arg0.format = __wbindgen_enum_GpuTextureFormat[arg1];
        }, arguments); },
        __wbg_set_format_713b9e90b13df6aa: function() { return logError(function (arg0, arg1) {
            arg0.format = __wbindgen_enum_GpuVertexFormat[arg1];
        }, arguments); },
        __wbg_set_format_76bcf93126fcdc9d: function() { return logError(function (arg0, arg1) {
            arg0.format = __wbindgen_enum_GpuTextureFormat[arg1];
        }, arguments); },
        __wbg_set_format_970299d3f84a8f20: function() { return logError(function (arg0, arg1) {
            arg0.format = __wbindgen_enum_GpuTextureFormat[arg1];
        }, arguments); },
        __wbg_set_format_a8a60feb127f0971: function() { return logError(function (arg0, arg1) {
            arg0.format = __wbindgen_enum_GpuTextureFormat[arg1];
        }, arguments); },
        __wbg_set_format_beb33029aea4cf8e: function() { return logError(function (arg0, arg1) {
            arg0.format = __wbindgen_enum_GpuTextureFormat[arg1];
        }, arguments); },
        __wbg_set_format_f6ec428901712514: function() { return logError(function (arg0, arg1) {
            arg0.format = __wbindgen_enum_GpuTextureFormat[arg1];
        }, arguments); },
        __wbg_set_fragment_0f23dfb67b3e84ab: function() { return logError(function (arg0, arg1) {
            arg0.fragment = arg1;
        }, arguments); },
        __wbg_set_front_face_c80337acd997f8c6: function() { return logError(function (arg0, arg1) {
            arg0.frontFace = __wbindgen_enum_GpuFrontFace[arg1];
        }, arguments); },
        __wbg_set_g_7eb6b5e67456a09e: function() { return logError(function (arg0, arg1) {
            arg0.g = arg1;
        }, arguments); },
        __wbg_set_has_dynamic_offset_b34dfdba692a7959: function() { return logError(function (arg0, arg1) {
            arg0.hasDynamicOffset = arg1 !== 0;
        }, arguments); },
        __wbg_set_height_a7439239ff109215: function() { return logError(function (arg0, arg1) {
            arg0.height = arg1 >>> 0;
        }, arguments); },
        __wbg_set_height_b386c0f603610637: function() { return logError(function (arg0, arg1) {
            arg0.height = arg1 >>> 0;
        }, arguments); },
        __wbg_set_height_f21f985387070100: function() { return logError(function (arg0, arg1) {
            arg0.height = arg1 >>> 0;
        }, arguments); },
        __wbg_set_label_0fab35538b0283a8: function() { return logError(function (arg0, arg1, arg2) {
            arg0.label = getStringFromWasm0(arg1, arg2);
        }, arguments); },
        __wbg_set_label_190cc9c7ee762bf6: function() { return logError(function (arg0, arg1, arg2) {
            arg0.label = getStringFromWasm0(arg1, arg2);
        }, arguments); },
        __wbg_set_label_1df8805b2aad72d7: function() { return logError(function (arg0, arg1, arg2) {
            arg0.label = getStringFromWasm0(arg1, arg2);
        }, arguments); },
        __wbg_set_label_42bf9d58f7b48944: function() { return logError(function (arg0, arg1, arg2) {
            arg0.label = getStringFromWasm0(arg1, arg2);
        }, arguments); },
        __wbg_set_label_460a52030d604dd7: function() { return logError(function (arg0, arg1, arg2) {
            arg0.label = getStringFromWasm0(arg1, arg2);
        }, arguments); },
        __wbg_set_label_57008c2e11276b5e: function() { return logError(function (arg0, arg1, arg2) {
            arg0.label = getStringFromWasm0(arg1, arg2);
        }, arguments); },
        __wbg_set_label_66db708c47a585b2: function() { return logError(function (arg0, arg1, arg2) {
            arg0.label = getStringFromWasm0(arg1, arg2);
        }, arguments); },
        __wbg_set_label_68cd87490e02e1de: function() { return logError(function (arg0, arg1, arg2) {
            arg0.label = getStringFromWasm0(arg1, arg2);
        }, arguments); },
        __wbg_set_label_76b058f0224eb49e: function() { return logError(function (arg0, arg1, arg2) {
            arg0.label = getStringFromWasm0(arg1, arg2);
        }, arguments); },
        __wbg_set_label_89c327fa94d8076b: function() { return logError(function (arg0, arg1, arg2) {
            arg0.label = getStringFromWasm0(arg1, arg2);
        }, arguments); },
        __wbg_set_label_969d6f8279c74456: function() { return logError(function (arg0, arg1, arg2) {
            arg0.label = getStringFromWasm0(arg1, arg2);
        }, arguments); },
        __wbg_set_label_a0c41069e355431e: function() { return logError(function (arg0, arg1, arg2) {
            arg0.label = getStringFromWasm0(arg1, arg2);
        }, arguments); },
        __wbg_set_label_c14214ffbf6e5c4a: function() { return logError(function (arg0, arg1, arg2) {
            arg0.label = getStringFromWasm0(arg1, arg2);
        }, arguments); },
        __wbg_set_label_ca2c132e2b646244: function() { return logError(function (arg0, arg1, arg2) {
            arg0.label = getStringFromWasm0(arg1, arg2);
        }, arguments); },
        __wbg_set_label_e47ee707d3281b5c: function() { return logError(function (arg0, arg1, arg2) {
            arg0.label = getStringFromWasm0(arg1, arg2);
        }, arguments); },
        __wbg_set_label_e6fab993e10f1dd3: function() { return logError(function (arg0, arg1, arg2) {
            arg0.label = getStringFromWasm0(arg1, arg2);
        }, arguments); },
        __wbg_set_label_f9a45e9ef445b781: function() { return logError(function (arg0, arg1, arg2) {
            arg0.label = getStringFromWasm0(arg1, arg2);
        }, arguments); },
        __wbg_set_layout_67a29edc6247c437: function() { return logError(function (arg0, arg1) {
            arg0.layout = arg1;
        }, arguments); },
        __wbg_set_layout_758d30edbd6ea91c: function() { return logError(function (arg0, arg1) {
            arg0.layout = arg1;
        }, arguments); },
        __wbg_set_layout_cade01d14a230b20: function() { return logError(function (arg0, arg1) {
            arg0.layout = arg1;
        }, arguments); },
        __wbg_set_load_op_5644a3bf70f4f76c: function() { return logError(function (arg0, arg1) {
            arg0.loadOp = __wbindgen_enum_GpuLoadOp[arg1];
        }, arguments); },
        __wbg_set_lod_max_clamp_d80060a9922f9fe3: function() { return logError(function (arg0, arg1) {
            arg0.lodMaxClamp = arg1;
        }, arguments); },
        __wbg_set_lod_min_clamp_bee469ae69d038f0: function() { return logError(function (arg0, arg1) {
            arg0.lodMinClamp = arg1;
        }, arguments); },
        __wbg_set_mag_filter_f50646cfdc01700d: function() { return logError(function (arg0, arg1) {
            arg0.magFilter = __wbindgen_enum_GpuFilterMode[arg1];
        }, arguments); },
        __wbg_set_mapped_at_creation_0dc5796d4e90ab4b: function() { return logError(function (arg0, arg1) {
            arg0.mappedAtCreation = arg1 !== 0;
        }, arguments); },
        __wbg_set_mask_800b15ad78613be8: function() { return logError(function (arg0, arg1) {
            arg0.mask = arg1 >>> 0;
        }, arguments); },
        __wbg_set_max_anisotropy_83ac2a8bef9f9ec8: function() { return logError(function (arg0, arg1) {
            arg0.maxAnisotropy = arg1;
        }, arguments); },
        __wbg_set_min_binding_size_20ca594cd6d93818: function() { return logError(function (arg0, arg1) {
            arg0.minBindingSize = arg1;
        }, arguments); },
        __wbg_set_min_filter_8ffc9e1ac6b4149f: function() { return logError(function (arg0, arg1) {
            arg0.minFilter = __wbindgen_enum_GpuFilterMode[arg1];
        }, arguments); },
        __wbg_set_mip_level_4e2a9d8b9b47208e: function() { return logError(function (arg0, arg1) {
            arg0.mipLevel = arg1 >>> 0;
        }, arguments); },
        __wbg_set_mip_level_6f507098915add77: function() { return logError(function (arg0, arg1) {
            arg0.mipLevel = arg1 >>> 0;
        }, arguments); },
        __wbg_set_mip_level_count_5e59806cbcf116e9: function() { return logError(function (arg0, arg1) {
            arg0.mipLevelCount = arg1 >>> 0;
        }, arguments); },
        __wbg_set_mip_level_count_f896fe8cbb669df2: function() { return logError(function (arg0, arg1) {
            arg0.mipLevelCount = arg1 >>> 0;
        }, arguments); },
        __wbg_set_mipmap_filter_037575f2e647f024: function() { return logError(function (arg0, arg1) {
            arg0.mipmapFilter = __wbindgen_enum_GpuMipmapFilterMode[arg1];
        }, arguments); },
        __wbg_set_module_4c73bb35cb0beb0b: function() { return logError(function (arg0, arg1) {
            arg0.module = arg1;
        }, arguments); },
        __wbg_set_module_7d5ff73dea7c42f9: function() { return logError(function (arg0, arg1) {
            arg0.module = arg1;
        }, arguments); },
        __wbg_set_module_ca21130b3f66ea5d: function() { return logError(function (arg0, arg1) {
            arg0.module = arg1;
        }, arguments); },
        __wbg_set_multisample_4f57dcaa4144a62f: function() { return logError(function (arg0, arg1) {
            arg0.multisample = arg1;
        }, arguments); },
        __wbg_set_multisampled_0bb9fc1b577bf11a: function() { return logError(function (arg0, arg1) {
            arg0.multisampled = arg1 !== 0;
        }, arguments); },
        __wbg_set_offset_67ee100819c122f2: function() { return logError(function (arg0, arg1) {
            arg0.offset = arg1;
        }, arguments); },
        __wbg_set_offset_721180fefc9711a9: function() { return logError(function (arg0, arg1) {
            arg0.offset = arg1;
        }, arguments); },
        __wbg_set_offset_a8194a4fcfff8910: function() { return logError(function (arg0, arg1) {
            arg0.offset = arg1;
        }, arguments); },
        __wbg_set_offset_d37e5fa34e9ded2e: function() { return logError(function (arg0, arg1) {
            arg0.offset = arg1;
        }, arguments); },
        __wbg_set_onclose_d382f3e2c2b850eb: function() { return logError(function (arg0, arg1) {
            arg0.onclose = arg1;
        }, arguments); },
        __wbg_set_onerror_377f18bf4569bf85: function() { return logError(function (arg0, arg1) {
            arg0.onerror = arg1;
        }, arguments); },
        __wbg_set_onmessage_2114aa5f4f53051e: function() { return logError(function (arg0, arg1) {
            arg0.onmessage = arg1;
        }, arguments); },
        __wbg_set_onopen_b7b52d519d6c0f11: function() { return logError(function (arg0, arg1) {
            arg0.onopen = arg1;
        }, arguments); },
        __wbg_set_onuncapturederror_3449cdb695f16431: function() { return logError(function (arg0, arg1) {
            arg0.onuncapturederror = arg1;
        }, arguments); },
        __wbg_set_operation_173958551af7f4f2: function() { return logError(function (arg0, arg1) {
            arg0.operation = __wbindgen_enum_GpuBlendOperation[arg1];
        }, arguments); },
        __wbg_set_origin_13b56d848aada680: function() { return logError(function (arg0, arg1) {
            arg0.origin = arg1;
        }, arguments); },
        __wbg_set_origin_e26b73e77b3e275d: function() { return logError(function (arg0, arg1) {
            arg0.origin = arg1;
        }, arguments); },
        __wbg_set_origin_f72dc9fdb8a63f0c: function() { return logError(function (arg0, arg1) {
            arg0.origin = arg1;
        }, arguments); },
        __wbg_set_pass_op_070547fd6160a00d: function() { return logError(function (arg0, arg1) {
            arg0.passOp = __wbindgen_enum_GpuStencilOperation[arg1];
        }, arguments); },
        __wbg_set_power_preference_1f3351e5d2acf765: function() { return logError(function (arg0, arg1) {
            arg0.powerPreference = __wbindgen_enum_GpuPowerPreference[arg1];
        }, arguments); },
        __wbg_set_premultiplied_alpha_de7d1cc1ae4ca1a8: function() { return logError(function (arg0, arg1) {
            arg0.premultipliedAlpha = arg1 !== 0;
        }, arguments); },
        __wbg_set_primitive_ee18492ab93953bc: function() { return logError(function (arg0, arg1) {
            arg0.primitive = arg1;
        }, arguments); },
        __wbg_set_query_set_3b14f95f9bd114db: function() { return logError(function (arg0, arg1) {
            arg0.querySet = arg1;
        }, arguments); },
        __wbg_set_query_set_4475a28689089d2c: function() { return logError(function (arg0, arg1) {
            arg0.querySet = arg1;
        }, arguments); },
        __wbg_set_r_a4e2f60e3466da86: function() { return logError(function (arg0, arg1) {
            arg0.r = arg1;
        }, arguments); },
        __wbg_set_required_features_fc44bc3433300ee3: function() { return logError(function (arg0, arg1) {
            arg0.requiredFeatures = arg1;
        }, arguments); },
        __wbg_set_resolve_target_c4b519cab7eb42b7: function() { return logError(function (arg0, arg1) {
            arg0.resolveTarget = arg1;
        }, arguments); },
        __wbg_set_resource_1659f5a29a2e0541: function() { return logError(function (arg0, arg1) {
            arg0.resource = arg1;
        }, arguments); },
        __wbg_set_rows_per_image_53ed2c633b1adfcc: function() { return logError(function (arg0, arg1) {
            arg0.rowsPerImage = arg1 >>> 0;
        }, arguments); },
        __wbg_set_rows_per_image_b16fc77b3e7f5230: function() { return logError(function (arg0, arg1) {
            arg0.rowsPerImage = arg1 >>> 0;
        }, arguments); },
        __wbg_set_sample_count_ce64315c0b08bd90: function() { return logError(function (arg0, arg1) {
            arg0.sampleCount = arg1 >>> 0;
        }, arguments); },
        __wbg_set_sample_count_e88d044f067a2241: function() { return logError(function (arg0, arg1) {
            arg0.sampleCount = arg1 >>> 0;
        }, arguments); },
        __wbg_set_sample_type_c0e25b966db74174: function() { return logError(function (arg0, arg1) {
            arg0.sampleType = __wbindgen_enum_GpuTextureSampleType[arg1];
        }, arguments); },
        __wbg_set_sampler_a778272f31d31ce5: function() { return logError(function (arg0, arg1) {
            arg0.sampler = arg1;
        }, arguments); },
        __wbg_set_shader_location_985046f48e76573f: function() { return logError(function (arg0, arg1) {
            arg0.shaderLocation = arg1 >>> 0;
        }, arguments); },
        __wbg_set_size_23676383c9c0732f: function() { return logError(function (arg0, arg1) {
            arg0.size = arg1;
        }, arguments); },
        __wbg_set_size_51616eaf8209c58b: function() { return logError(function (arg0, arg1) {
            arg0.size = arg1;
        }, arguments); },
        __wbg_set_size_5878aadcd23673cf: function() { return logError(function (arg0, arg1) {
            arg0.size = arg1;
        }, arguments); },
        __wbg_set_source_b1e66b73aa8a4ebc: function() { return logError(function (arg0, arg1) {
            arg0.source = arg1;
        }, arguments); },
        __wbg_set_src_factor_04ce8874f1bff5a8: function() { return logError(function (arg0, arg1) {
            arg0.srcFactor = __wbindgen_enum_GpuBlendFactor[arg1];
        }, arguments); },
        __wbg_set_stencil_back_4b20ecfcd4c4816a: function() { return logError(function (arg0, arg1) {
            arg0.stencilBack = arg1;
        }, arguments); },
        __wbg_set_stencil_clear_value_7ba82e1993788f37: function() { return logError(function (arg0, arg1) {
            arg0.stencilClearValue = arg1 >>> 0;
        }, arguments); },
        __wbg_set_stencil_front_1ca3b695f7c42f6a: function() { return logError(function (arg0, arg1) {
            arg0.stencilFront = arg1;
        }, arguments); },
        __wbg_set_stencil_load_op_b65c60a0077315cd: function() { return logError(function (arg0, arg1) {
            arg0.stencilLoadOp = __wbindgen_enum_GpuLoadOp[arg1];
        }, arguments); },
        __wbg_set_stencil_read_mask_4f5b98747141e796: function() { return logError(function (arg0, arg1) {
            arg0.stencilReadMask = arg1 >>> 0;
        }, arguments); },
        __wbg_set_stencil_read_only_6a18fc38e0d8494b: function() { return logError(function (arg0, arg1) {
            arg0.stencilReadOnly = arg1 !== 0;
        }, arguments); },
        __wbg_set_stencil_read_only_9006a99a91d198e9: function() { return logError(function (arg0, arg1) {
            arg0.stencilReadOnly = arg1 !== 0;
        }, arguments); },
        __wbg_set_stencil_store_op_4f00c5eca345c145: function() { return logError(function (arg0, arg1) {
            arg0.stencilStoreOp = __wbindgen_enum_GpuStoreOp[arg1];
        }, arguments); },
        __wbg_set_stencil_write_mask_e37a7214d84ace99: function() { return logError(function (arg0, arg1) {
            arg0.stencilWriteMask = arg1 >>> 0;
        }, arguments); },
        __wbg_set_step_mode_7d58d75e6547a7a6: function() { return logError(function (arg0, arg1) {
            arg0.stepMode = __wbindgen_enum_GpuVertexStepMode[arg1];
        }, arguments); },
        __wbg_set_storage_texture_2987339fec972d54: function() { return logError(function (arg0, arg1) {
            arg0.storageTexture = arg1;
        }, arguments); },
        __wbg_set_store_op_c62dd050b5806095: function() { return logError(function (arg0, arg1) {
            arg0.storeOp = __wbindgen_enum_GpuStoreOp[arg1];
        }, arguments); },
        __wbg_set_strip_index_format_3e4893749b3f00b0: function() { return logError(function (arg0, arg1) {
            arg0.stripIndexFormat = __wbindgen_enum_GpuIndexFormat[arg1];
        }, arguments); },
        __wbg_set_targets_0ef1de33af7253a6: function() { return logError(function (arg0, arg1) {
            arg0.targets = arg1;
        }, arguments); },
        __wbg_set_textContent_3e87dba095d9cdbc: function() { return logError(function (arg0, arg1, arg2) {
            arg0.textContent = arg1 === 0 ? undefined : getStringFromWasm0(arg1, arg2);
        }, arguments); },
        __wbg_set_texture_2553e9c3ae6f7687: function() { return logError(function (arg0, arg1) {
            arg0.texture = arg1;
        }, arguments); },
        __wbg_set_texture_28ef6c52713faba9: function() { return logError(function (arg0, arg1) {
            arg0.texture = arg1;
        }, arguments); },
        __wbg_set_texture_f62859f817324dd1: function() { return logError(function (arg0, arg1) {
            arg0.texture = arg1;
        }, arguments); },
        __wbg_set_timestamp_writes_1995524c3a31cb8f: function() { return logError(function (arg0, arg1) {
            arg0.timestampWrites = arg1;
        }, arguments); },
        __wbg_set_timestamp_writes_bebe8db3de77d9e1: function() { return logError(function (arg0, arg1) {
            arg0.timestampWrites = arg1;
        }, arguments); },
        __wbg_set_topology_3d9b2f0ffe2e350c: function() { return logError(function (arg0, arg1) {
            arg0.topology = __wbindgen_enum_GpuPrimitiveTopology[arg1];
        }, arguments); },
        __wbg_set_type_0b59dd5f4721c490: function() { return logError(function (arg0, arg1) {
            arg0.type = __wbindgen_enum_GpuSamplerBindingType[arg1];
        }, arguments); },
        __wbg_set_type_8c8bbfab4cf7e32e: function() { return logError(function (arg0, arg1) {
            arg0.type = __wbindgen_enum_GpuBufferBindingType[arg1];
        }, arguments); },
        __wbg_set_type_e1183496fe921f94: function() { return logError(function (arg0, arg1) {
            arg0.type = __wbindgen_enum_GpuQueryType[arg1];
        }, arguments); },
        __wbg_set_usage_44ebc3b496e60ff4: function() { return logError(function (arg0, arg1) {
            arg0.usage = arg1 >>> 0;
        }, arguments); },
        __wbg_set_usage_4cf7b16df5617a46: function() { return logError(function (arg0, arg1) {
            arg0.usage = arg1 >>> 0;
        }, arguments); },
        __wbg_set_usage_c45cca4a5b9f8376: function() { return logError(function (arg0, arg1) {
            arg0.usage = arg1 >>> 0;
        }, arguments); },
        __wbg_set_usage_e58b3c3ce83fbbda: function() { return logError(function (arg0, arg1) {
            arg0.usage = arg1 >>> 0;
        }, arguments); },
        __wbg_set_vertex_6144c56d98e2314a: function() { return logError(function (arg0, arg1) {
            arg0.vertex = arg1;
        }, arguments); },
        __wbg_set_view_4bc3dfcbfc8a58ba: function() { return logError(function (arg0, arg1) {
            arg0.view = arg1;
        }, arguments); },
        __wbg_set_view_8d0b0055b6ef07e3: function() { return logError(function (arg0, arg1) {
            arg0.view = arg1;
        }, arguments); },
        __wbg_set_view_dimension_afac48443b8fb565: function() { return logError(function (arg0, arg1) {
            arg0.viewDimension = __wbindgen_enum_GpuTextureViewDimension[arg1];
        }, arguments); },
        __wbg_set_view_dimension_f5d4b5336a27d302: function() { return logError(function (arg0, arg1) {
            arg0.viewDimension = __wbindgen_enum_GpuTextureViewDimension[arg1];
        }, arguments); },
        __wbg_set_view_formats_0cfe174ac882efaf: function() { return logError(function (arg0, arg1) {
            arg0.viewFormats = arg1;
        }, arguments); },
        __wbg_set_view_formats_c566feb1da7b1925: function() { return logError(function (arg0, arg1) {
            arg0.viewFormats = arg1;
        }, arguments); },
        __wbg_set_visibility_7245f1acbedb4ff4: function() { return logError(function (arg0, arg1) {
            arg0.visibility = arg1 >>> 0;
        }, arguments); },
        __wbg_set_width_056381a7176ba440: function() { return logError(function (arg0, arg1) {
            arg0.width = arg1 >>> 0;
        }, arguments); },
        __wbg_set_width_7f07715a20503914: function() { return logError(function (arg0, arg1) {
            arg0.width = arg1 >>> 0;
        }, arguments); },
        __wbg_set_width_d60bc4f2f20c56a4: function() { return logError(function (arg0, arg1) {
            arg0.width = arg1 >>> 0;
        }, arguments); },
        __wbg_set_write_mask_c381ff702509999c: function() { return logError(function (arg0, arg1) {
            arg0.writeMask = arg1 >>> 0;
        }, arguments); },
        __wbg_set_x_6e550cba86f408f0: function() { return logError(function (arg0, arg1) {
            arg0.x = arg1 >>> 0;
        }, arguments); },
        __wbg_set_x_941ab227b0ea435d: function() { return logError(function (arg0, arg1) {
            arg0.x = arg1 >>> 0;
        }, arguments); },
        __wbg_set_y_16ff3ff771600f8c: function() { return logError(function (arg0, arg1) {
            arg0.y = arg1 >>> 0;
        }, arguments); },
        __wbg_set_y_e9ed0be0aad66dd7: function() { return logError(function (arg0, arg1) {
            arg0.y = arg1 >>> 0;
        }, arguments); },
        __wbg_set_z_b2c09b24c996ee06: function() { return logError(function (arg0, arg1) {
            arg0.z = arg1 >>> 0;
        }, arguments); },
        __wbg_size_73bdfb6d5ffd9c4b: function() { return logError(function (arg0) {
            const ret = arg0.size;
            return ret;
        }, arguments); },
        __wbg_stack_0ed75d68575b0f3c: function() { return logError(function (arg0, arg1) {
            const ret = arg1.stack;
            const ptr1 = passStringToWasm0(ret, wasm.__wbindgen_malloc, wasm.__wbindgen_realloc);
            const len1 = WASM_VECTOR_LEN;
            getDataViewMemory0().setInt32(arg0 + 4 * 1, len1, true);
            getDataViewMemory0().setInt32(arg0 + 4 * 0, ptr1, true);
        }, arguments); },
        __wbg_static_accessor_GLOBAL_12837167ad935116: function() { return logError(function () {
            const ret = typeof global === 'undefined' ? null : global;
            return isLikeNone(ret) ? 0 : addToExternrefTable0(ret);
        }, arguments); },
        __wbg_static_accessor_GLOBAL_THIS_e628e89ab3b1c95f: function() { return logError(function () {
            const ret = typeof globalThis === 'undefined' ? null : globalThis;
            return isLikeNone(ret) ? 0 : addToExternrefTable0(ret);
        }, arguments); },
        __wbg_static_accessor_SELF_a621d3dfbb60d0ce: function() { return logError(function () {
            const ret = typeof self === 'undefined' ? null : self;
            return isLikeNone(ret) ? 0 : addToExternrefTable0(ret);
        }, arguments); },
        __wbg_static_accessor_WINDOW_f8727f0cf888e0bd: function() { return logError(function () {
            const ret = typeof window === 'undefined' ? null : window;
            return isLikeNone(ret) ? 0 : addToExternrefTable0(ret);
        }, arguments); },
        __wbg_submit_252766c4e0945cee: function() { return logError(function (arg0, arg1) {
            arg0.submit(arg1);
        }, arguments); },
        __wbg_then_0d9fe2c7b1857d32: function() { return logError(function (arg0, arg1, arg2) {
            const ret = arg0.then(arg1, arg2);
            return ret;
        }, arguments); },
        __wbg_then_b9e7b3b5f1a9e1b5: function() { return logError(function (arg0, arg1) {
            const ret = arg0.then(arg1);
            return ret;
        }, arguments); },
        __wbg_unmap_7b299155f31a9d79: function() { return logError(function (arg0) {
            arg0.unmap();
        }, arguments); },
        __wbg_usage_7d38adc6eaf96849: function() { return logError(function (arg0) {
            const ret = arg0.usage;
            _assertNum(ret);
            return ret;
        }, arguments); },
        __wbg_valueOf_3c28600026e653c4: function() { return logError(function (arg0) {
            const ret = arg0.valueOf();
            return ret;
        }, arguments); },
        __wbg_value_0546255b415e96c1: function() { return logError(function (arg0) {
            const ret = arg0.value;
            return ret;
        }, arguments); },
        __wbg_warn_f7ae1b2e66ccb930: function() { return logError(function (arg0) {
            console.warn(arg0);
        }, arguments); },
        __wbg_wgslLanguageFeatures_95d24c58747b65ed: function() { return logError(function (arg0) {
            const ret = arg0.wgslLanguageFeatures;
            return ret;
        }, arguments); },
        __wbg_width_5f66bde2e810fbde: function() { return logError(function (arg0) {
            const ret = arg0.width;
            _assertNum(ret);
            return ret;
        }, arguments); },
        __wbg_width_ae46cb8e98ee102f: function() { return logError(function (arg0) {
            const ret = arg0.width;
            return ret;
        }, arguments); },
        __wbg_writeBuffer_3193eaacefdcf39a: function() { return handleError(function (arg0, arg1, arg2, arg3, arg4, arg5) {
            arg0.writeBuffer(arg1, arg2, arg3, arg4, arg5);
        }, arguments); },
        __wbg_writeTexture_cd7877c213ee5704: function() { return handleError(function (arg0, arg1, arg2, arg3, arg4) {
            arg0.writeTexture(arg1, arg2, arg3, arg4);
        }, arguments); },
        __wbindgen_cast_0000000000000001: function() { return logError(function (arg0, arg1) {
            // Cast intrinsic for `Closure(Closure { dtor_idx: 2, function: Function { arguments: [F64], shim_idx: 10, ret: Unit, inner_ret: Some(Unit) }, mutable: true }) -> Externref`.
            const ret = makeMutClosure(arg0, arg1, wasm.wasm_bindgen__closure__destroy__ha157ccf0ab72b46c, wasm_bindgen__convert__closures_____invoke__h9e0a4c62f8bc48d7);
            return ret;
        }, arguments); },
        __wbindgen_cast_0000000000000002: function() { return logError(function (arg0, arg1) {
            // Cast intrinsic for `Closure(Closure { dtor_idx: 288, function: Function { arguments: [NamedExternref("GPUUncapturedErrorEvent")], shim_idx: 284, ret: Unit, inner_ret: Some(Unit) }, mutable: true }) -> Externref`.
            const ret = makeMutClosure(arg0, arg1, wasm.wasm_bindgen__closure__destroy__he41d28c1907a046e, wasm_bindgen__convert__closures_____invoke__h666172b7eeeeb412);
            return ret;
        }, arguments); },
        __wbindgen_cast_0000000000000003: function() { return logError(function (arg0, arg1) {
            // Cast intrinsic for `Closure(Closure { dtor_idx: 293, function: Function { arguments: [Externref], shim_idx: 294, ret: Unit, inner_ret: Some(Unit) }, mutable: true }) -> Externref`.
            const ret = makeMutClosure(arg0, arg1, wasm.wasm_bindgen__closure__destroy__hb205f5f9f90dccf6, wasm_bindgen__convert__closures_____invoke__h630e19bc80c22d01);
            return ret;
        }, arguments); },
        __wbindgen_cast_0000000000000004: function() { return logError(function (arg0, arg1) {
            // Cast intrinsic for `Closure(Closure { dtor_idx: 3, function: Function { arguments: [NamedExternref("MessageEvent")], shim_idx: 9, ret: Unit, inner_ret: Some(Unit) }, mutable: true }) -> Externref`.
            const ret = makeMutClosure(arg0, arg1, wasm.wasm_bindgen__closure__destroy__he58f27e7277a0bce, wasm_bindgen__convert__closures_____invoke__h850daf4f85c35d83);
            return ret;
        }, arguments); },
        __wbindgen_cast_0000000000000005: function() { return logError(function (arg0, arg1) {
            // Cast intrinsic for `Closure(Closure { dtor_idx: 4, function: Function { arguments: [NamedExternref("Event")], shim_idx: 8, ret: Unit, inner_ret: Some(Unit) }, mutable: true }) -> Externref`.
            const ret = makeMutClosure(arg0, arg1, wasm.wasm_bindgen__closure__destroy__h4a728242c61dcfa9, wasm_bindgen__convert__closures_____invoke__he0158893042d4229);
            return ret;
        }, arguments); },
        __wbindgen_cast_0000000000000006: function() { return logError(function (arg0) {
            // Cast intrinsic for `F64 -> Externref`.
            const ret = arg0;
            return ret;
        }, arguments); },
        __wbindgen_cast_0000000000000007: function() { return logError(function (arg0, arg1) {
            // Cast intrinsic for `Ref(Slice(U8)) -> NamedExternref("Uint8Array")`.
            const ret = getArrayU8FromWasm0(arg0, arg1);
            return ret;
        }, arguments); },
        __wbindgen_cast_0000000000000008: function() { return logError(function (arg0, arg1) {
            // Cast intrinsic for `Ref(String) -> Externref`.
            const ret = getStringFromWasm0(arg0, arg1);
            return ret;
        }, arguments); },
        __wbindgen_init_externref_table: function() {
            const table = wasm.__wbindgen_externrefs;
            const offset = table.grow(4);
            table.set(0, undefined);
            table.set(offset + 0, undefined);
            table.set(offset + 1, null);
            table.set(offset + 2, true);
            table.set(offset + 3, false);
        },
    };
    return {
        __proto__: null,
        "./radar_web_client_bg.js": import0,
    };
}


//#endregion
function wasm_bindgen__convert__closures_____invoke__h4ce9ffda94ce5582(arg0, arg1) {
    _assertNum(arg0);
    _assertNum(arg1);
    const ret = wasm.wasm_bindgen__convert__closures_____invoke__h4ce9ffda94ce5582(arg0, arg1);
    return ret !== 0;
}

function wasm_bindgen__convert__closures_____invoke__h666172b7eeeeb412(arg0, arg1, arg2) {
    _assertNum(arg0);
    _assertNum(arg1);
    wasm.wasm_bindgen__convert__closures_____invoke__h666172b7eeeeb412(arg0, arg1, arg2);
}

function wasm_bindgen__convert__closures_____invoke__h630e19bc80c22d01(arg0, arg1, arg2) {
    _assertNum(arg0);
    _assertNum(arg1);
    wasm.wasm_bindgen__convert__closures_____invoke__h630e19bc80c22d01(arg0, arg1, arg2);
}

function wasm_bindgen__convert__closures_____invoke__h850daf4f85c35d83(arg0, arg1, arg2) {
    _assertNum(arg0);
    _assertNum(arg1);
    wasm.wasm_bindgen__convert__closures_____invoke__h850daf4f85c35d83(arg0, arg1, arg2);
}

function wasm_bindgen__convert__closures_____invoke__he0158893042d4229(arg0, arg1, arg2) {
    _assertNum(arg0);
    _assertNum(arg1);
    wasm.wasm_bindgen__convert__closures_____invoke__he0158893042d4229(arg0, arg1, arg2);
}

function wasm_bindgen__convert__closures_____invoke__h9e0a4c62f8bc48d7(arg0, arg1, arg2) {
    _assertNum(arg0);
    _assertNum(arg1);
    wasm.wasm_bindgen__convert__closures_____invoke__h9e0a4c62f8bc48d7(arg0, arg1, arg2);
}


const __wbindgen_enum_BinaryType = ["blob", "arraybuffer"];


const __wbindgen_enum_GpuAddressMode = ["clamp-to-edge", "repeat", "mirror-repeat"];


const __wbindgen_enum_GpuBlendFactor = ["zero", "one", "src", "one-minus-src", "src-alpha", "one-minus-src-alpha", "dst", "one-minus-dst", "dst-alpha", "one-minus-dst-alpha", "src-alpha-saturated", "constant", "one-minus-constant", "src1", "one-minus-src1", "src1-alpha", "one-minus-src1-alpha"];


const __wbindgen_enum_GpuBlendOperation = ["add", "subtract", "reverse-subtract", "min", "max"];


const __wbindgen_enum_GpuBufferBindingType = ["uniform", "storage", "read-only-storage"];


const __wbindgen_enum_GpuCanvasAlphaMode = ["opaque", "premultiplied"];


const __wbindgen_enum_GpuCompareFunction = ["never", "less", "equal", "less-equal", "greater", "not-equal", "greater-equal", "always"];


const __wbindgen_enum_GpuCullMode = ["none", "front", "back"];


const __wbindgen_enum_GpuDeviceLostReason = ["unknown", "destroyed"];


const __wbindgen_enum_GpuErrorFilter = ["validation", "out-of-memory", "internal"];


const __wbindgen_enum_GpuFilterMode = ["nearest", "linear"];


const __wbindgen_enum_GpuFrontFace = ["ccw", "cw"];


const __wbindgen_enum_GpuIndexFormat = ["uint16", "uint32"];


const __wbindgen_enum_GpuLoadOp = ["load", "clear"];


const __wbindgen_enum_GpuMipmapFilterMode = ["nearest", "linear"];


const __wbindgen_enum_GpuPowerPreference = ["low-power", "high-performance"];


const __wbindgen_enum_GpuPrimitiveTopology = ["point-list", "line-list", "line-strip", "triangle-list", "triangle-strip"];


const __wbindgen_enum_GpuQueryType = ["occlusion", "timestamp"];


const __wbindgen_enum_GpuSamplerBindingType = ["filtering", "non-filtering", "comparison"];


const __wbindgen_enum_GpuStencilOperation = ["keep", "zero", "replace", "invert", "increment-clamp", "decrement-clamp", "increment-wrap", "decrement-wrap"];


const __wbindgen_enum_GpuStorageTextureAccess = ["write-only", "read-only", "read-write"];


const __wbindgen_enum_GpuStoreOp = ["store", "discard"];


const __wbindgen_enum_GpuTextureAspect = ["all", "stencil-only", "depth-only"];


const __wbindgen_enum_GpuTextureDimension = ["1d", "2d", "3d"];


const __wbindgen_enum_GpuTextureFormat = ["r8unorm", "r8snorm", "r8uint", "r8sint", "r16uint", "r16sint", "r16float", "rg8unorm", "rg8snorm", "rg8uint", "rg8sint", "r32uint", "r32sint", "r32float", "rg16uint", "rg16sint", "rg16float", "rgba8unorm", "rgba8unorm-srgb", "rgba8snorm", "rgba8uint", "rgba8sint", "bgra8unorm", "bgra8unorm-srgb", "rgb9e5ufloat", "rgb10a2uint", "rgb10a2unorm", "rg11b10ufloat", "rg32uint", "rg32sint", "rg32float", "rgba16uint", "rgba16sint", "rgba16float", "rgba32uint", "rgba32sint", "rgba32float", "stencil8", "depth16unorm", "depth24plus", "depth24plus-stencil8", "depth32float", "depth32float-stencil8", "bc1-rgba-unorm", "bc1-rgba-unorm-srgb", "bc2-rgba-unorm", "bc2-rgba-unorm-srgb", "bc3-rgba-unorm", "bc3-rgba-unorm-srgb", "bc4-r-unorm", "bc4-r-snorm", "bc5-rg-unorm", "bc5-rg-snorm", "bc6h-rgb-ufloat", "bc6h-rgb-float", "bc7-rgba-unorm", "bc7-rgba-unorm-srgb", "etc2-rgb8unorm", "etc2-rgb8unorm-srgb", "etc2-rgb8a1unorm", "etc2-rgb8a1unorm-srgb", "etc2-rgba8unorm", "etc2-rgba8unorm-srgb", "eac-r11unorm", "eac-r11snorm", "eac-rg11unorm", "eac-rg11snorm", "astc-4x4-unorm", "astc-4x4-unorm-srgb", "astc-5x4-unorm", "astc-5x4-unorm-srgb", "astc-5x5-unorm", "astc-5x5-unorm-srgb", "astc-6x5-unorm", "astc-6x5-unorm-srgb", "astc-6x6-unorm", "astc-6x6-unorm-srgb", "astc-8x5-unorm", "astc-8x5-unorm-srgb", "astc-8x6-unorm", "astc-8x6-unorm-srgb", "astc-8x8-unorm", "astc-8x8-unorm-srgb", "astc-10x5-unorm", "astc-10x5-unorm-srgb", "astc-10x6-unorm", "astc-10x6-unorm-srgb", "astc-10x8-unorm", "astc-10x8-unorm-srgb", "astc-10x10-unorm", "astc-10x10-unorm-srgb", "astc-12x10-unorm", "astc-12x10-unorm-srgb", "astc-12x12-unorm", "astc-12x12-unorm-srgb"];


const __wbindgen_enum_GpuTextureSampleType = ["float", "unfilterable-float", "depth", "sint", "uint"];


const __wbindgen_enum_GpuTextureViewDimension = ["1d", "2d", "2d-array", "cube", "cube-array", "3d"];


const __wbindgen_enum_GpuVertexFormat = ["uint8", "uint8x2", "uint8x4", "sint8", "sint8x2", "sint8x4", "unorm8", "unorm8x2", "unorm8x4", "snorm8", "snorm8x2", "snorm8x4", "uint16", "uint16x2", "uint16x4", "sint16", "sint16x2", "sint16x4", "unorm16", "unorm16x2", "unorm16x4", "snorm16", "snorm16x2", "snorm16x4", "float16", "float16x2", "float16x4", "float32", "float32x2", "float32x3", "float32x4", "uint32", "uint32x2", "uint32x3", "uint32x4", "sint32", "sint32x2", "sint32x3", "sint32x4", "unorm10-10-10-2", "unorm8x4-bgra"];


const __wbindgen_enum_GpuVertexStepMode = ["vertex", "instance"];


//#region intrinsics
function addToExternrefTable0(obj) {
    const idx = wasm.__externref_table_alloc();
    wasm.__wbindgen_externrefs.set(idx, obj);
    return idx;
}

function _assertBoolean(n) {
    if (typeof(n) !== 'boolean') {
        throw new Error(`expected a boolean argument, found ${typeof(n)}`);
    }
}

function _assertNum(n) {
    if (typeof(n) !== 'number') throw new Error(`expected a number argument, found ${typeof(n)}`);
}

const CLOSURE_DTORS = (typeof FinalizationRegistry === 'undefined')
    ? { register: () => {}, unregister: () => {} }
    : new FinalizationRegistry(state => state.dtor(state.a, state.b));

function debugString(val) {
    // primitive types
    const type = typeof val;
    if (type == 'number' || type == 'boolean' || val == null) {
        return  `${val}`;
    }
    if (type == 'string') {
        return `"${val}"`;
    }
    if (type == 'symbol') {
        const description = val.description;
        if (description == null) {
            return 'Symbol';
        } else {
            return `Symbol(${description})`;
        }
    }
    if (type == 'function') {
        const name = val.name;
        if (typeof name == 'string' && name.length > 0) {
            return `Function(${name})`;
        } else {
            return 'Function';
        }
    }
    // objects
    if (Array.isArray(val)) {
        const length = val.length;
        let debug = '[';
        if (length > 0) {
            debug += debugString(val[0]);
        }
        for(let i = 1; i < length; i++) {
            debug += ', ' + debugString(val[i]);
        }
        debug += ']';
        return debug;
    }
    // Test for built-in
    const builtInMatches = /\[object ([^\]]+)\]/.exec(toString.call(val));
    let className;
    if (builtInMatches && builtInMatches.length > 1) {
        className = builtInMatches[1];
    } else {
        // Failed to match the standard '[object ClassName]'
        return toString.call(val);
    }
    if (className == 'Object') {
        // we're a user defined class or Object
        // JSON.stringify avoids problems with cycles, and is generally much
        // easier than looping through ownProperties of `val`.
        try {
            return 'Object(' + JSON.stringify(val) + ')';
        } catch (_) {
            return 'Object';
        }
    }
    // errors
    if (val instanceof Error) {
        return `${val.name}: ${val.message}\n${val.stack}`;
    }
    // TODO we could test for more things here, like `Set`s and `Map`s.
    return className;
}

function getArrayU32FromWasm0(ptr, len) {
    ptr = ptr >>> 0;
    return getUint32ArrayMemory0().subarray(ptr / 4, ptr / 4 + len);
}

function getArrayU8FromWasm0(ptr, len) {
    ptr = ptr >>> 0;
    return getUint8ArrayMemory0().subarray(ptr / 1, ptr / 1 + len);
}

let cachedDataViewMemory0 = null;
function getDataViewMemory0() {
    if (cachedDataViewMemory0 === null || cachedDataViewMemory0.buffer.detached === true || (cachedDataViewMemory0.buffer.detached === undefined && cachedDataViewMemory0.buffer !== wasm.memory.buffer)) {
        cachedDataViewMemory0 = new DataView(wasm.memory.buffer);
    }
    return cachedDataViewMemory0;
}

function getStringFromWasm0(ptr, len) {
    ptr = ptr >>> 0;
    return decodeText(ptr, len);
}

let cachedUint32ArrayMemory0 = null;
function getUint32ArrayMemory0() {
    if (cachedUint32ArrayMemory0 === null || cachedUint32ArrayMemory0.byteLength === 0) {
        cachedUint32ArrayMemory0 = new Uint32Array(wasm.memory.buffer);
    }
    return cachedUint32ArrayMemory0;
}

let cachedUint8ArrayMemory0 = null;
function getUint8ArrayMemory0() {
    if (cachedUint8ArrayMemory0 === null || cachedUint8ArrayMemory0.byteLength === 0) {
        cachedUint8ArrayMemory0 = new Uint8Array(wasm.memory.buffer);
    }
    return cachedUint8ArrayMemory0;
}

function handleError(f, args) {
    try {
        return f.apply(this, args);
    } catch (e) {
        const idx = addToExternrefTable0(e);
        wasm.__wbindgen_exn_store(idx);
    }
}

function isLikeNone(x) {
    return x === undefined || x === null;
}

function logError(f, args) {
    try {
        return f.apply(this, args);
    } catch (e) {
        let error = (function () {
            try {
                return e instanceof Error ? `${e.message}\n\nStack:\n${e.stack}` : e.toString();
            } catch(_) {
                return "<failed to stringify thrown value>";
            }
        }());
        console.error("wasm-bindgen: imported JS function that was not marked as `catch` threw an error:", error);
        throw e;
    }
}

function makeMutClosure(arg0, arg1, dtor, f) {
    const state = { a: arg0, b: arg1, cnt: 1, dtor };
    const real = (...args) => {

        // First up with a closure we increment the internal reference
        // count. This ensures that the Rust closure environment won't
        // be deallocated while we're invoking it.
        state.cnt++;
        const a = state.a;
        state.a = 0;
        try {
            return f(a, state.b, ...args);
        } finally {
            state.a = a;
            real._wbg_cb_unref();
        }
    };
    real._wbg_cb_unref = () => {
        if (--state.cnt === 0) {
            state.dtor(state.a, state.b);
            state.a = 0;
            CLOSURE_DTORS.unregister(state);
        }
    };
    CLOSURE_DTORS.register(real, state, state);
    return real;
}

function passStringToWasm0(arg, malloc, realloc) {
    if (typeof(arg) !== 'string') throw new Error(`expected a string argument, found ${typeof(arg)}`);
    if (realloc === undefined) {
        const buf = cachedTextEncoder.encode(arg);
        const ptr = malloc(buf.length, 1) >>> 0;
        getUint8ArrayMemory0().subarray(ptr, ptr + buf.length).set(buf);
        WASM_VECTOR_LEN = buf.length;
        return ptr;
    }

    let len = arg.length;
    let ptr = malloc(len, 1) >>> 0;

    const mem = getUint8ArrayMemory0();

    let offset = 0;

    for (; offset < len; offset++) {
        const code = arg.charCodeAt(offset);
        if (code > 0x7F) break;
        mem[ptr + offset] = code;
    }
    if (offset !== len) {
        if (offset !== 0) {
            arg = arg.slice(offset);
        }
        ptr = realloc(ptr, len, len = offset + arg.length * 3, 1) >>> 0;
        const view = getUint8ArrayMemory0().subarray(ptr + offset, ptr + len);
        const ret = cachedTextEncoder.encodeInto(arg, view);
        if (ret.read !== arg.length) throw new Error('failed to pass whole string');
        offset += ret.written;
        ptr = realloc(ptr, len, offset, 1) >>> 0;
    }

    WASM_VECTOR_LEN = offset;
    return ptr;
}

let cachedTextDecoder = new TextDecoder('utf-8', { ignoreBOM: true, fatal: true });
cachedTextDecoder.decode();
const MAX_SAFARI_DECODE_BYTES = 2146435072;
let numBytesDecoded = 0;
function decodeText(ptr, len) {
    numBytesDecoded += len;
    if (numBytesDecoded >= MAX_SAFARI_DECODE_BYTES) {
        cachedTextDecoder = new TextDecoder('utf-8', { ignoreBOM: true, fatal: true });
        cachedTextDecoder.decode();
        numBytesDecoded = len;
    }
    return cachedTextDecoder.decode(getUint8ArrayMemory0().subarray(ptr, ptr + len));
}

const cachedTextEncoder = new TextEncoder();

if (!('encodeInto' in cachedTextEncoder)) {
    cachedTextEncoder.encodeInto = function (arg, view) {
        const buf = cachedTextEncoder.encode(arg);
        view.set(buf);
        return {
            read: arg.length,
            written: buf.length
        };
    };
}

let WASM_VECTOR_LEN = 0;


//#endregion

//#region wasm loading
let wasmModule, wasm;
function __wbg_finalize_init(instance, module) {
    wasm = instance.exports;
    wasmModule = module;
    cachedDataViewMemory0 = null;
    cachedUint32ArrayMemory0 = null;
    cachedUint8ArrayMemory0 = null;
    wasm.__wbindgen_start();
    return wasm;
}

async function __wbg_load(module, imports) {
    if (typeof Response === 'function' && module instanceof Response) {
        if (typeof WebAssembly.instantiateStreaming === 'function') {
            try {
                return await WebAssembly.instantiateStreaming(module, imports);
            } catch (e) {
                const validResponse = module.ok && expectedResponseType(module.type);

                if (validResponse && module.headers.get('Content-Type') !== 'application/wasm') {
                    console.warn("`WebAssembly.instantiateStreaming` failed because your server does not serve Wasm with `application/wasm` MIME type. Falling back to `WebAssembly.instantiate` which is slower. Original error:\n", e);

                } else { throw e; }
            }
        }

        const bytes = await module.arrayBuffer();
        return await WebAssembly.instantiate(bytes, imports);
    } else {
        const instance = await WebAssembly.instantiate(module, imports);

        if (instance instanceof WebAssembly.Instance) {
            return { instance, module };
        } else {
            return instance;
        }
    }

    function expectedResponseType(type) {
        switch (type) {
            case 'basic': case 'cors': case 'default': return true;
        }
        return false;
    }
}

function initSync(module) {
    if (wasm !== undefined) return wasm;


    if (module !== undefined) {
        if (Object.getPrototypeOf(module) === Object.prototype) {
            ({module} = module)
        } else {
            console.warn('using deprecated parameters for `initSync()`; pass a single object instead')
        }
    }

    const imports = __wbg_get_imports();
    if (!(module instanceof WebAssembly.Module)) {
        module = new WebAssembly.Module(module);
    }
    const instance = new WebAssembly.Instance(module, imports);
    return __wbg_finalize_init(instance, module);
}

async function __wbg_init(module_or_path) {
    if (wasm !== undefined) return wasm;


    if (module_or_path !== undefined) {
        if (Object.getPrototypeOf(module_or_path) === Object.prototype) {
            ({module_or_path} = module_or_path)
        } else {
            console.warn('using deprecated parameters for the initialization function; pass a single object instead')
        }
    }

    if (module_or_path === undefined) {
        module_or_path = new URL('radar_web_client_bg.wasm', import.meta.url);
    }
    const imports = __wbg_get_imports();

    if (typeof module_or_path === 'string' || (typeof Request === 'function' && module_or_path instanceof Request) || (typeof URL === 'function' && module_or_path instanceof URL)) {
        module_or_path = fetch(module_or_path);
    }

    const { instance, module } = await __wbg_load(await module_or_path, imports);

    return __wbg_finalize_init(instance, module);
}

export { initSync, __wbg_init as default };
//#endregion
export { wasm as __wasm }
