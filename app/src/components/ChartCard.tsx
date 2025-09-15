import React from "react";
import { Platform } from "react-native";
import { Card, Text } from "react-native-paper";

// Use 'victory' on web and 'victory-native' on native
const { VictoryChart, VictoryLine, VictoryAxis } =
  Platform.OS === "web" ? require("victory") : require("victory-native");

type Point = { day: string; revenue: number };

type Props = {
  title?: string;
  data: Point[];
  x?: keyof Point;
  y?: keyof Point;
  subtitle?: string;
};

export default function ChartCard({
  title = "Revenue Over Time",
  data,
  x = "day",
  y = "revenue",
  subtitle
}: Props) {
  return (
    <Card style={{ marginTop: 12, padding: 12 }}>
      <Text variant="titleLarge">{title}</Text>
      {subtitle ? <Text style={{ marginBottom: 8 }}>{subtitle}</Text> : null}
      <VictoryChart domainPadding={12}>
        <VictoryAxis tickFormat={(t: any) => String(t).slice(5)} />
        <VictoryLine data={data} x={String(x)} y={String(y)} />
      </VictoryChart>
    </Card>
  );
}
