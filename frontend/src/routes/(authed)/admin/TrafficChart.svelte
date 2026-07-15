<script lang="ts">
  import type { DailyTraffic } from "$lib/analytics";
  import { max, sum } from "d3-array";
  import { scaleLinear, scaleUtc } from "d3-scale";
  import { area, curveMonotoneX, line } from "d3-shape";
  import { onMount } from "svelte";

  type ChartPoint = DailyTraffic & {
    dateValue: Date;
  };

  let { data }: { data: DailyTraffic[] } = $props();

  let container: HTMLElement;
  let observedWidth = $state(0);
  let activeIndex = $state<number | null>(null);

  const numberFormatter = new Intl.NumberFormat("en-DK");
  const axisDateFormatter = new Intl.DateTimeFormat("en-DK", {
    weekday: "short",
    day: "numeric",
    timeZone: "UTC"
  });
  const longDateFormatter = new Intl.DateTimeFormat("en-DK", {
    weekday: "short",
    month: "short",
    day: "numeric",
    timeZone: "UTC"
  });

  const margin = {
    top: 18,
    right: 12,
    bottom: 38,
    left: 42
  } as const;

  let points = $derived.by((): ChartPoint[] => {
    const parsed: ChartPoint[] = [];

    for (const day of data) {
      const dateValue = new Date(`${day.date}T00:00:00Z`);
      if (!Number.isNaN(dateValue.valueOf())) {
        parsed.push({ ...day, dateValue });
      }
    }

    return parsed.sort((left, right) => left.dateValue.valueOf() - right.dateValue.valueOf());
  });

  let chartWidth = $derived(Math.max(260, observedWidth || 640));
  let chartHeight = $derived(chartWidth < 480 ? 248 : 286);
  let plotRight = $derived(chartWidth - margin.right);
  let plotBottom = $derived(chartHeight - margin.bottom);

  let xDomain = $derived.by((): [Date, Date] => {
    const first = points[0]?.dateValue;
    const last = points.at(-1)?.dateValue;
    if (!first || !last) {
      return [new Date(0), new Date(86_400_000)];
    }

    if (first.valueOf() === last.valueOf()) {
      return [new Date(first.valueOf() - 43_200_000), new Date(last.valueOf() + 43_200_000)];
    }

    return [first, last];
  });

  let yMaximum = $derived(
    max(points, (point) => Math.max(point.page_views, point.browser_sessions)) ?? 0
  );
  let xScale = $derived.by(() => scaleUtc().domain(xDomain).range([margin.left, plotRight]));
  let yScale = $derived.by(() =>
    scaleLinear()
      .domain([0, Math.max(1, yMaximum)])
      .nice(4)
      .range([plotBottom, margin.top])
  );

  let yTicks = $derived(
    yScale
      .ticks(4)
      .filter(Number.isInteger)
      .filter((tick, index, ticks) => index === 0 || tick !== ticks[index - 1])
  );
  let xTickPoints = $derived.by(() => {
    const target = chartWidth < 390 ? 3 : chartWidth < 620 ? 4 : 7;
    return sampleEvenly(points, target);
  });

  let pageViewArea = $derived(
    area<ChartPoint>()
      .x((point) => xScale(point.dateValue))
      .y0(plotBottom)
      .y1((point) => yScale(point.page_views))
      .curve(curveMonotoneX)(points) ?? ""
  );
  let pageViewLine = $derived(
    line<ChartPoint>()
      .x((point) => xScale(point.dateValue))
      .y((point) => yScale(point.page_views))
      .curve(curveMonotoneX)(points) ?? ""
  );
  let sessionLine = $derived(
    line<ChartPoint>()
      .x((point) => xScale(point.dateValue))
      .y((point) => yScale(point.browser_sessions))
      .curve(curveMonotoneX)(points) ?? ""
  );

  let totalPageViews = $derived(sum(points, (point) => point.page_views));
  let totalSessions = $derived(sum(points, (point) => point.browser_sessions));
  let busiestDay = $derived.by(() => {
    if (points.length === 0 || totalPageViews === 0) return null;
    return points.reduce((busiest, point) =>
      point.page_views > busiest.page_views ? point : busiest
    );
  });
  let chartSummary = $derived.by(() => {
    if (points.length === 0) return "No daily traffic has been recorded.";

    const dateRange = `${formatLongDate(points[0].dateValue)} to ${formatLongDate(points.at(-1)!.dateValue)}`;
    const peak = busiestDay
      ? ` The busiest day was ${formatLongDate(busiestDay.dateValue)} with ${formatCount(busiestDay.page_views)} page views.`
      : "";

    return `Daily traffic from ${dateRange}: ${formatCount(totalPageViews)} page views and ${formatCount(totalSessions)} tab sessions.${peak}`;
  });

  let activePoint = $derived(activeIndex === null ? null : (points[activeIndex] ?? null));
  let tooltipWidth = $derived(chartWidth < 390 ? 134 : 154);
  let tooltipX = $derived(
    activePoint
      ? Math.min(
          plotRight - tooltipWidth,
          Math.max(margin.left, xScale(activePoint.dateValue) + 10)
        )
      : margin.left
  );

  onMount(() => {
    if (typeof ResizeObserver === "undefined") return;

    const observer = new ResizeObserver(([entry]) => {
      const nextWidth = Math.round(entry?.contentRect.width ?? 0);
      if (nextWidth > 0 && nextWidth !== observedWidth) {
        observedWidth = nextWidth;
      }
    });

    observer.observe(container);
    return () => observer.disconnect();
  });

  function formatCount(value: number) {
    return numberFormatter.format(value);
  }

  function formatLongDate(value: Date) {
    return longDateFormatter.format(value);
  }

  function sampleEvenly(values: ChartPoint[], target: number): ChartPoint[] {
    if (values.length <= target) return values;

    const indexes = Array.from({ length: target }, (_, index) =>
      Math.round((index * (values.length - 1)) / (target - 1))
    );
    return indexes
      .filter((value, index) => index === 0 || value !== indexes[index - 1])
      .map((index) => values[index]);
  }

  function hitAreaStart(index: number) {
    const current = xScale(points[index].dateValue);
    if (index === 0) return margin.left;
    return (xScale(points[index - 1].dateValue) + current) / 2;
  }

  function hitAreaEnd(index: number) {
    const current = xScale(points[index].dateValue);
    if (index === points.length - 1) return plotRight;
    return (current + xScale(points[index + 1].dateValue)) / 2;
  }
</script>

<figure bind:this={container} class="min-w-0">
  <div class="mb-3 flex flex-wrap items-center gap-x-5 gap-y-2 text-xs font-medium">
    <span class="flex items-center gap-2">
      <span class="bg-primary h-0.5 w-6 rounded-full" aria-hidden="true"></span>
      Page views
    </span>
    <span class="text-muted-foreground flex items-center gap-2">
      <span class="border-muted-foreground h-0 w-6 border-t-2 border-dashed" aria-hidden="true"
      ></span>
      Tab sessions
    </span>
  </div>

  <svg
    class="block h-auto w-full overflow-visible"
    viewBox={`0 0 ${chartWidth} ${chartHeight}`}
    role="img"
    aria-label={chartSummary}
    onpointerleave={() => (activeIndex = null)}
  >
    <title>Daily traffic</title>
    <desc>{chartSummary}</desc>

    {#each yTicks as tick (tick)}
      {@const y = yScale(tick)}
      <line
        x1={margin.left}
        x2={plotRight}
        y1={y}
        y2={y}
        stroke="hsl(var(--border))"
        stroke-width="1"
        stroke-dasharray={tick === 0 ? undefined : "3 4"}
        vector-effect="non-scaling-stroke"
      />
      <text
        x={margin.left - 9}
        {y}
        dy="0.32em"
        text-anchor="end"
        fill="hsl(var(--muted-foreground))"
        font-size="10"
        class="tabular-nums">{formatCount(tick)}</text
      >
    {/each}

    {#each xTickPoints as point, index (point.date)}
      {@const x = xScale(point.dateValue)}
      <line
        x1={x}
        x2={x}
        y1={plotBottom}
        y2={plotBottom + 5}
        stroke="hsl(var(--border))"
        stroke-width="1"
        vector-effect="non-scaling-stroke"
      />
      <text
        {x}
        y={plotBottom + 20}
        text-anchor={index === 0 ? "start" : index === xTickPoints.length - 1 ? "end" : "middle"}
        fill="hsl(var(--muted-foreground))"
        font-size="10">{axisDateFormatter.format(point.dateValue)}</text
      >
    {/each}

    <path d={pageViewArea} fill="hsl(var(--primary))" fill-opacity="0.1" pointer-events="none" />
    <path
      d={pageViewLine}
      fill="none"
      stroke="hsl(var(--primary))"
      stroke-width="2.5"
      stroke-linecap="round"
      stroke-linejoin="round"
      vector-effect="non-scaling-stroke"
      pointer-events="none"
    />
    <path
      d={sessionLine}
      fill="none"
      stroke="hsl(var(--muted-foreground))"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
      stroke-dasharray="5 4"
      vector-effect="non-scaling-stroke"
      pointer-events="none"
    />

    {#each points as point (point.date)}
      <circle
        cx={xScale(point.dateValue)}
        cy={yScale(point.page_views)}
        r="3.5"
        fill="hsl(var(--card))"
        stroke="hsl(var(--primary))"
        stroke-width="2"
        vector-effect="non-scaling-stroke"
        pointer-events="none"
      />
      <circle
        cx={xScale(point.dateValue)}
        cy={yScale(point.browser_sessions)}
        r="3"
        fill="hsl(var(--card))"
        stroke="hsl(var(--muted-foreground))"
        stroke-width="1.75"
        vector-effect="non-scaling-stroke"
        pointer-events="none"
      />
    {/each}

    {#each points as point, index (point.date)}
      <rect
        x={hitAreaStart(index)}
        y={margin.top}
        width={Math.max(1, hitAreaEnd(index) - hitAreaStart(index))}
        height={plotBottom - margin.top}
        fill="transparent"
        aria-hidden="true"
        onpointerenter={() => (activeIndex = index)}
        onpointerdown={() => (activeIndex = index)}
      />
    {/each}

    {#if activePoint}
      <g pointer-events="none">
        <line
          x1={xScale(activePoint.dateValue)}
          x2={xScale(activePoint.dateValue)}
          y1={margin.top}
          y2={plotBottom}
          stroke="hsl(var(--foreground))"
          stroke-opacity="0.22"
          stroke-width="1"
          vector-effect="non-scaling-stroke"
        />
        <rect
          x={tooltipX}
          y={margin.top + 6}
          width={tooltipWidth}
          height="64"
          rx="8"
          fill="hsl(var(--popover))"
          stroke="hsl(var(--border))"
          stroke-width="1"
          vector-effect="non-scaling-stroke"
        />
        <text
          x={tooltipX + 10}
          y={margin.top + 23}
          fill="hsl(var(--popover-foreground))"
          font-size="10"
          font-weight="600">{formatLongDate(activePoint.dateValue)}</text
        >
        <circle cx={tooltipX + 12} cy={margin.top + 40} r="2.5" fill="hsl(var(--primary))" />
        <text
          x={tooltipX + 20}
          y={margin.top + 43}
          fill="hsl(var(--muted-foreground))"
          font-size="10">Page views</text
        >
        <text
          x={tooltipX + tooltipWidth - 10}
          y={margin.top + 43}
          text-anchor="end"
          fill="hsl(var(--popover-foreground))"
          font-size="10"
          font-weight="600">{formatCount(activePoint.page_views)}</text
        >
        <circle
          cx={tooltipX + 12}
          cy={margin.top + 57}
          r="2.5"
          fill="hsl(var(--muted-foreground))"
        />
        <text
          x={tooltipX + 20}
          y={margin.top + 60}
          fill="hsl(var(--muted-foreground))"
          font-size="10">Tab sessions</text
        >
        <text
          x={tooltipX + tooltipWidth - 10}
          y={margin.top + 60}
          text-anchor="end"
          fill="hsl(var(--popover-foreground))"
          font-size="10"
          font-weight="600">{formatCount(activePoint.browser_sessions)}</text
        >
      </g>
    {/if}
  </svg>

  <table class="sr-only">
    <caption>Daily traffic values</caption>
    <thead>
      <tr>
        <th scope="col">Date</th>
        <th scope="col">Page views</th>
        <th scope="col">Tab sessions</th>
      </tr>
    </thead>
    <tbody>
      {#each points as point (point.date)}
        <tr>
          <th scope="row">{formatLongDate(point.dateValue)}</th>
          <td>{formatCount(point.page_views)}</td>
          <td>{formatCount(point.browser_sessions)}</td>
        </tr>
      {/each}
    </tbody>
  </table>

  <figcaption
    class="text-muted-foreground mt-1 flex flex-wrap items-center justify-between gap-x-4 gap-y-1 text-xs"
  >
    <span>{points.length} UTC calendar days</span>
    {#if busiestDay}
      <span>
        Peak: {formatCount(busiestDay.page_views)} views on {formatLongDate(busiestDay.dateValue)}
      </span>
    {/if}
  </figcaption>
</figure>
