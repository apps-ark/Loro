import { UploadZone } from "@/components/upload/UploadZone";

export default function HomePage() {
  return (
    <div>
      <h1 className="mb-2 text-center text-2xl font-bold">
        Loro
      </h1>
      <p className="mb-8 text-center text-gray-500">
        Sube una entrevista en ingles y obten la traduccion al espanol con las
        voces originales
      </p>
      <UploadZone />
    </div>
  );
}
