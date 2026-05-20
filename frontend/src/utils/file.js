/**
 * 文件工具。
 *
 * 上传队列需要稳定识别同一个本地文件，不能只依赖文件名。
 */
/** 生成文件唯一标识 */
export const fileKey = (file) => `${file.name}|${file.size}|${file.lastModified}`
