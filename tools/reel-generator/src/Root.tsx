import { Composition } from "remotion";
import { BalmoralReel } from "./BalmoralReel";
import { CaseStudyReel } from "./CaseStudyReel";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="BalmoralReel"
        component={BalmoralReel}
        durationInFrames={23 * 30} // 23 seconds
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="CaseStudyReel"
        component={CaseStudyReel}
        durationInFrames={48 * 30} // 48 seconds
        fps={30}
        width={1080}
        height={1920}
      />
    </>
  );
};
