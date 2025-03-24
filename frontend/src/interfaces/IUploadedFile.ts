import { UploadedFileStatus } from "@/enums";

export default interface IUploadedFile {
  latestFileName: string;
  uploadTimestamp: number;
  fileNameOnUpload: string;
  sizeInByte: number;
  status: UploadedFileStatus;
  transcriptionUrl: string
}
