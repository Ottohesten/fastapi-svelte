export interface RealtimeDrinkLink {
    drink_id: string;
    drink_name: string | null;
    amount: number;
}

export interface RealtimePlayer {
    id: string;
    name: string;
    team_id: string | null;
    drinks: RealtimeDrinkLink[];
}

export interface RealtimeTeam {
    id: string;
    name: string;
    player_ids: string[];
}

export interface GameRealtimeSnapshot {
    id: string;
    title: string;
    players: RealtimePlayer[];
    teams: RealtimeTeam[];
}

export type GameRealtimeMessage =
    | { type: 'snapshot'; data: GameRealtimeSnapshot }
    | { type: 'update'; data: GameRealtimeSnapshot }
    | { type: 'error'; detail: string };
