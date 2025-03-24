import FileUploader from "@/components/FileUploader";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

export default function Home() {
  const getAllTranscriptsAPIUrl =
    import.meta.env.VITE_API_ORIGIN_URL + "/transcriptions";
  const [files, setFiles] = useState<File[]>([] as File[]);

  const getAllTranscripts = () =>
    fetch(getAllTranscriptsAPIUrl, {
      method: "GET",
    });

  const { data, isLoading, isError } = useQuery({
    queryKey: ["transcriptions"],
    queryFn: getAllTranscripts,
  });
  console.log(data);
  return (
    <div>
      <FileUploader
        files={files}
        setFiles={setFiles}
        uploadFileUrl="/transcribe"
        acceptedFiles={{
          "audio/mpeg": [".mp3"],
        }}
      />
      <div>
        <div>Available Transcriptions</div>
        <div className="bg-gray-100"></div>
      </div>
    </div>
  );
}
