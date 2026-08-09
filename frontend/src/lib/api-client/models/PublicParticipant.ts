/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CursorPosition } from './CursorPosition';
import type { Role } from './Role';
/**
 * Participant fields safe to expose through a bearer session link.
 */
export type PublicParticipant = {
    avatar?: (string | null);
    color?: (string | null);
    cursorPosition?: (CursorPosition | null);
    isTyping?: boolean;
    joinedAt: string;
    role: Role;
    username: string;
};

