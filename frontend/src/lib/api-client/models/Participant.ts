/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CursorPosition } from './CursorPosition';
export type Participant = {
    id?: string;
    username?: string;
    avatar?: string;
    role?: Participant.role;
    cursorPosition?: CursorPosition;
    isTyping?: boolean;
    color?: string;
    joinedAt?: string;
};
export namespace Participant {
    export enum role {
        HOST = 'host',
        PARTICIPANT = 'participant',
        SPECTATOR = 'spectator',
    }
}

