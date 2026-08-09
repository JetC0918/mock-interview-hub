/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CursorPosition } from './CursorPosition';
import type { Role } from './Role';
export type Participant = {
    avatar?: (string | null);
    color?: (string | null);
    cursorPosition?: (CursorPosition | null);
    id: string;
    isTyping?: boolean;
    joinedAt: string;
    role: Role;
    username: string;
};

