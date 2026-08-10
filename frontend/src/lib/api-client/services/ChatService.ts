/* Compatibility facade for older frontend imports.
 * Chat endpoints are now generated under SessionsService because they share
 * the /sessions/{id} resource. */
import type { CancelablePromise } from '../core/CancelablePromise';
import type { ChatMessage } from '../models/ChatMessage';
import type { ChatMessageCreate } from '../models/ChatMessageCreate';
import { SessionsService } from './SessionsService';

export class ChatService {
    public static postSessionsMessages(id: string, requestBody: ChatMessageCreate): CancelablePromise<ChatMessage> {
        return SessionsService.sendMessageSessionsIdMessagesPost({ id, requestBody });
    }

    public static getSessionsMessages(id: string): CancelablePromise<Array<ChatMessage>> {
        return SessionsService.getMessagesSessionsIdMessagesGet({ id });
    }
}
