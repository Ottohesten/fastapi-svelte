import { error } from "@sveltejs/kit";
import type { PageServerLoad } from "./$types";

export const load: PageServerLoad = async ({ parent, params }) => {
    const parentData = await parent();
    const gameSession = parentData.game_session;

    if (!gameSession) {
        error(404, "Game session not found");
    }

    const team = gameSession.teams.find(
        (candidate) =>
            candidate.id === params.team_id && candidate.game_session_id === gameSession.id
    );

    if (!team) {
        error(404, "Team not found in this game session");
    }

    return {
        team,
        players: gameSession.players.filter((player) => player.team_id === team.id)
    };
};
