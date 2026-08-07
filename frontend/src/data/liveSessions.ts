import type { ChatMessage, ExecutionResult, Session } from '@/lib/api';

const minutesAgo = (minutes: number) => new Date(Date.now() - minutes * 60_000);

export const demoLiveSessions: Session[] = [
  {
    id: 'live-1',
    pin: '789456',
    hostId: 'host-1',
    title: 'Senior Frontend Interview',
    description: 'A live TypeScript interview focused on data structures and communication.',
    language: 'typescript',
    participants: [
      {
        id: 'p1',
        username: 'interviewer_jane',
        role: 'host',
        color: 'hsl(174 72% 50%)',
        joinedAt: minutesAgo(38),
      },
      {
        id: 'p2',
        username: 'candidate_mike',
        role: 'participant',
        color: 'hsl(265 70% 60%)',
        cursorPosition: { line: 14, column: 7 },
        isTyping: true,
        joinedAt: minutesAgo(36),
      },
    ],
    code: `type Interval = [number, number];

function mergeIntervals(intervals: Interval[]): Interval[] {
  if (intervals.length <= 1) return intervals;

  intervals.sort((a, b) => a[0] - b[0]);
  const merged: Interval[] = [intervals[0]];

  for (let i = 1; i < intervals.length; i++) {
    const current = intervals[i];
    const previous = merged[merged.length - 1];

    if (current[0] <= previous[1]) {
      previous[1] = Math.max(previous[1], current[1]);
    } else {
      merged.push(current);
    }
  }

  return merged;
}`,
    status: 'active',
    createdAt: minutesAgo(38),
    problem: {
      id: 'merge-intervals',
      title: 'Merge Intervals',
      description:
        'Given an array of intervals where intervals[i] = [startᵢ, endᵢ], merge all overlapping intervals and return the non-overlapping intervals that cover every interval in the input.',
      examples: [
        {
          input: '[[1,3],[2,6],[8,10],[15,18]]',
          output: '[[1,6],[8,10],[15,18]]',
          explanation: '[1,3] and [2,6] overlap, so they are merged into [1,6].',
        },
        {
          input: '[[1,4],[4,5]]',
          output: '[[1,5]]',
        },
      ],
      constraints: [
        '1 ≤ intervals.length ≤ 10⁴',
        'intervals[i].length == 2',
        '0 ≤ startᵢ ≤ endᵢ ≤ 10⁴',
      ],
      difficulty: 'medium',
    },
  },
  {
    id: 'live-2',
    pin: '321654',
    hostId: 'host-2',
    title: 'Algorithm Challenge',
    description: 'A Python session working through graph traversal.',
    language: 'python',
    participants: [
      { id: 'p3', username: 'coach_sara', role: 'host', color: 'hsl(174 72% 50%)', joinedAt: minutesAgo(45) },
      { id: 'p4', username: 'student_alex', role: 'participant', color: 'hsl(38 92% 50%)', joinedAt: minutesAgo(43) },
      { id: 'p5', username: 'student_emma', role: 'participant', color: 'hsl(330 80% 60%)', joinedAt: minutesAgo(41) },
    ],
    code: `def shortest_path(graph, start, end):
    queue = [(start, [start])]
    visited = {start}

    while queue:
        node, path = queue.pop(0)
        if node == end:
            return path

        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))

    return []`,
    status: 'active',
    createdAt: minutesAgo(45),
  },
  {
    id: 'live-3',
    pin: '654987',
    hostId: 'host-3',
    title: 'Bootcamp Live Session',
    description: 'A JavaScript bootcamp session on array transformations.',
    language: 'javascript',
    participants: [
      { id: 'p6', username: 'instructor', role: 'host', color: 'hsl(174 72% 50%)', joinedAt: minutesAgo(15) },
      { id: 'p7', username: 'student_1', role: 'participant', color: 'hsl(265 70% 60%)', joinedAt: minutesAgo(14) },
      { id: 'p8', username: 'student_2', role: 'participant', color: 'hsl(38 92% 50%)', joinedAt: minutesAgo(13) },
      { id: 'p9', username: 'student_3', role: 'participant', color: 'hsl(330 80% 60%)', joinedAt: minutesAgo(12) },
    ],
    code: `function groupByStatus(records) {
  return records.reduce((groups, record) => {
    const status = record.status ?? 'unknown';
    groups[status] ??= [];
    groups[status].push(record);
    return groups;
  }, {});
}`,
    status: 'active',
    createdAt: minutesAgo(15),
  },
];

const demoMessages: Record<string, ChatMessage[]> = {
  'live-1': [
    {
      id: 'm1',
      participantId: 'p1',
      username: 'interviewer_jane',
      message: 'Start by telling me what structure you want the output to have.',
      timestamp: minutesAgo(17),
    },
    {
      id: 'm2',
      participantId: 'p2',
      username: 'candidate_mike',
      message: 'I’ll sort by start time, then keep one merged interval as I scan.',
      timestamp: minutesAgo(15),
    },
    {
      id: 'm3',
      participantId: 'p1',
      username: 'interviewer_jane',
      message: 'Can you walk me through the complexity?',
      timestamp: minutesAgo(4),
    },
    {
      id: 'm4',
      participantId: 'p2',
      username: 'candidate_mike',
      message: 'Sorting dominates at O(n log n); the merge pass is O(n), with O(n) output space.',
      timestamp: minutesAgo(2),
    },
  ],
};

export const demoExecutionResult: ExecutionResult = {
  stdout: '✓ example 1\n✓ touching intervals\n✓ single interval\n\n3 tests passed',
  stderr: '',
  exitCode: 0,
  executionTime: 42,
};

export const getDemoLiveSession = (sessionId: string) =>
  demoLiveSessions.find((session) => session.id === sessionId) ?? null;

export const getDemoLiveMessages = (sessionId: string) => demoMessages[sessionId] ?? [];
