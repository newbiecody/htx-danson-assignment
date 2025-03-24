import { Dispatch, SetStateAction, useState } from "react";
import { Accept, useDropzone } from "react-dropzone";
import { useQuery, useMutation } from "@tanstack/react-query";
import { formatDateToHumanReadable } from "@/utils";
import { LoadingSpinner } from "./Spinner";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faChevronUp, faTimes } from "@fortawesome/free-solid-svg-icons";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@radix-ui/react-tooltip";

interface IFileUploader {
  acceptedFiles: Accept;
  uploadFileUrl: string;
  files: File[];
  setFiles: Dispatch<SetStateAction<File[]>>;
}

export default function FileUploader({
  acceptedFiles,
  uploadFileUrl,
  files,
  setFiles,
}: IFileUploader) {
  const fetchURL = import.meta.env.VITE_API_ORIGIN_URL + uploadFileUrl;
  const [uploadedFiles, setUploadedFiles] = useState();
  const uploadFiles = () => {
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append("files", files[i]);
    }
    return fetch(fetchURL, {
      method: "POST",
      body: formData,
    });
  };
  const {
    data: uploadResponse,
    isPending: isUploading,
    isError: uploadFailed,
    isSuccess: filesUploaded,
    mutate: commenceUpload,
  } = useMutation({
    mutationFn: uploadFiles,
  });

  const { getRootProps, getInputProps } = useDropzone({
    accept: acceptedFiles,
    onDrop: (acceptedFiles: File[]) => {
      setFiles(acceptedFiles);
      commenceUpload();
    },
  });

  return (
    <div className="flex flex-col gap-y-2">
      <div
        {...getRootProps()}
        className="p-4 border-2 border-dashed border-gray-300 rounded-md cursor-pointer"
      >
        <input {...getInputProps()} />
        <div className="text-center text-gray-500">
          Drag & drop files here, or click to select
        </div>
      </div>

      <div>
        {files && files?.length > 0 && (
          <div className="flex flex-col gap-y-2">
            {files.map((file, index) => (
              <div
                className="flex rounded-lg bg-gray-100 px-4 py-2 justify-between items-center"
                key={`${file.name}-${index}`}
              >
                <div>
                  <div className="flex gap-4">
                    <div> {file.name} </div>
                    <div> {(file.size / 1024).toFixed(2)} KB </div>
                  </div>
                  <div className="flex gap-2 text-sm">
                    {Object.entries(
                      formatDateToHumanReadable(file.lastModified)
                    ).map(([type, value]) => (
                      <div key={type}>{value}</div>
                    ))}
                  </div>
                </div>
                {isUploading && <LoadingSpinner />}
                {uploadFailed && (
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <FontAwesomeIcon
                          className="text-red-500"
                          icon={faTimes}
                        />
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>File upload failed</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
