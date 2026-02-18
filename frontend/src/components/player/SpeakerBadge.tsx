import { Badge } from "@/components/ui/badge";
import { getSpeakerColor } from "@/lib/constants";

interface Props {
  speaker: string;
}

export function SpeakerBadge({ speaker }: Props) {
  const colors = getSpeakerColor(speaker);
  const label = speaker.replace("SPEAKER_", "Hablante ");

  return (
    <Badge variant="outline" className={`${colors.bg} ${colors.text} ${colors.border} text-xs font-medium`}>
      {label}
    </Badge>
  );
}
