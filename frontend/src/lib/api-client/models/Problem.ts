/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type Problem = {
    id?: string;
    title?: string;
    description?: string;
    examples?: Array<{
        input?: string;
        output?: string;
        explanation?: string;
    }>;
    constraints?: Array<string>;
    difficulty?: Problem.difficulty;
};
export namespace Problem {
    export enum difficulty {
        EASY = 'easy',
        MEDIUM = 'medium',
        HARD = 'hard',
    }
}

