import { Composition } from "remotion";
import { BalmoralReel } from "./BalmoralReel";
import { CaseStudyReel } from "./CaseStudyReel";
import { WhatIDoReel } from "./WhatIDoReel";
import { PerchReel } from "./PerchReel";
import { PerchCaseStudy } from "./PerchCaseStudy";
import { PerchVideoReel } from "./PerchVideoReel";
import { DripHopReel } from "./DripHopReel";
import { PerchDripHop } from "./PerchDripHop";
import { BookingPost } from "./BookingPost";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="BookingPost"
        component={BookingPost}
        durationInFrames={1}
        fps={30}
        width={1080}
        height={1350}
      />
      <Composition
        id="PerchDripHop"
        component={PerchDripHop}
        durationInFrames={28 * 30}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="DripHopReel"
        component={DripHopReel}
        durationInFrames={32 * 30}
        fps={30}
        width={1080}
        height={1920}
      />
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
      <Composition
        id="WhatIDoReel"
        component={WhatIDoReel}
        durationInFrames={28 * 30} // 28 seconds
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="PerchReel"
        component={PerchReel}
        durationInFrames={40 * 30} // 40 seconds
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="PerchCaseStudy"
        component={PerchCaseStudy}
        durationInFrames={50 * 30} // 50 seconds
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="PerchVideoReel"
        component={PerchVideoReel}
        durationInFrames={50 * 30} // 50 seconds
        fps={30}
        width={1080}
        height={1920}
      />
    </>
  );
};
