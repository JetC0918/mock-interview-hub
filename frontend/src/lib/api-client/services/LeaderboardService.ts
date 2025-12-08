/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { LeaderboardEntry } from '../models/LeaderboardEntry';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class LeaderboardService {
    /**
     * Get leaderboard
     * @returns LeaderboardEntry Leaderboard data
     * @throws ApiError
     */
    public static getLeaderboard(): CancelablePromise<Array<LeaderboardEntry>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/leaderboard',
        });
    }
}
