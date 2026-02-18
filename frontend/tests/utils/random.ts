export const randomEmail = () => `test_${Math.random().toString(36).substring(7)}@example.com`;

export const randomTeamName = () => `Team ${Math.random().toString(36).substring(7)}`;

export const randomPassword = () => `${Math.random().toString(36).substring(2)}`;

export const randomSessionTitle = () =>
    `Playwright Session ${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

export const randomPlayerName = () => `Player ${Math.random().toString(36).slice(2, 8)}`;

export const randomPlayerNames = (count: number) =>
    Array.from({ length: count }, () => randomPlayerName());

export type PlayerSeed = {
    name: string;
    teamName: string;
};

export const randomPlayersForTeams = (teamNames: string[], playersPerTeam: number): PlayerSeed[] =>
    teamNames.flatMap((teamName) =>
        Array.from({ length: playersPerTeam }, () => ({
            name: randomPlayerName(),
            teamName
        }))
    );

export const slugify = (text: string) =>
    text
        .toLowerCase()
        .replace(/\s+/g, "-")
        .replace(/[^\w-]+/g, "");
