/**
 * =============================================================
 * PushNotifications - Push Notification Service
 * =============================================================
 * Handles push notifications for iOS and Android
 */

import { PushNotifications } from '@capacitor/push-notifications';
import { LocalNotifications } from '@capacitor/local-notifications';

/**
 * Request permission for push notifications
 * @returns {Promise<boolean>} Permission granted status
 */
export async function requestPermission() {
  try {
    const result = await PushNotifications.requestPermissions();
    return result.receive === 'granted';
  } catch (error) {
    console.error('Push notification permission error:', error);
    return false;
  }
}

/**
 * Check if permission has been granted
 * @returns {Promise<boolean>} Permission status
 */
export async function checkPermission() {
  try {
    const result = await PushNotifications.checkPermissions();
    return result.receive === 'granted';
  } catch (error) {
    console.error('Check push notification permission error:', error);
    return false;
  }
}

/**
 * Register for push notifications
 * @returns {Promise<string|null>} Registration token
 */
export async function register() {
  try {
    await PushNotifications.register();
    return new Promise((resolve, reject) => {
      const registrationHandler = (token) => {
        PushNotifications.removeAllListeners();
        resolve(token.value);
      };

      const registrationError = (error) => {
        PushNotifications.removeAllListeners();
        reject(error);
      };

      PushNotifications.addListener('registration', registrationHandler);
      PushNotifications.addListener('registrationError', registrationError);

      // Timeout after 30 seconds
      setTimeout(() => {
        PushNotifications.removeAllListeners();
        reject(new Error('Registration timeout'));
      }, 30000);
    });
  } catch (error) {
    console.error('Push notification registration error:', error);
    return null;
  }
}

/**
 * Unregister from push notifications
 */
export async function unregister() {
  try {
    await PushNotifications.unregister();
    await PushNotifications.removeAllListeners();
  } catch (error) {
    console.error('Push notification unregister error:', error);
  }
}

/**
 * Add listener for incoming push notifications
 * @param {Function} callback - Callback function for notifications
 */
export async function addNotificationListener(callback) {
  try {
    await PushNotifications.addListener('pushNotificationReceived', (notification) => {
      callback(notification);
    });
  } catch (error) {
    console.error('Add notification listener error:', error);
  }
}

/**
 * Add listener for notificationActionPerformed (user taps notification)
 * @param {Function} callback - Callback function
 */
export async function addActionListener(callback) {
  try {
    await PushNotifications.addListener('pushNotificationActionPerformed', (action) => {
      callback(action);
    });
  } catch (error) {
    console.error('Add action listener error:', error);
  }
}

/**
 * Schedule a local notification
 * @param {Object} options - Notification options
 */
export async function scheduleLocalNotification(options) {
  try {
    // Check permissions first
    const permissions = await LocalNotifications.checkPermissions();
    if (permissions.display !== 'granted') {
      await LocalNotifications.requestPermissions();
    }

    const notifications = [{
      id: options.id || Date.now(),
      title: options.title || 'NexControl',
      body: options.body || '',
      schedule: options.schedule,
      sound: options.sound || 'beep.wav',
      attachments: options.attachments,
      actionTypeId: options.actionTypeId,
      extra: options.extra || {}
    }];

    await LocalNotifications.schedule({ notifications });
    return true;
  } catch (error) {
    console.error('Schedule local notification error:', error);
    return false;
  }
}

/**
 * Cancel a scheduled local notification
 * @param {number[]} ids - Notification IDs to cancel
 */
export async function cancelLocalNotification(ids) {
  try {
    await LocalNotifications.cancel({ notifications: ids });
  } catch (error) {
    console.error('Cancel local notification error:', error);
  }
}

/**
 * Get all pending local notifications
 * @returns {Promise<Array>} List of pending notifications
 */
export async function getPendingNotifications() {
  try {
    const result = await LocalNotifications.getPending();
    return result.notifications || [];
  } catch (error) {
    console.error('Get pending notifications error:', error);
    return [];
  }
}

/**
 * Add listener for local notification action
 * @param {Function} callback - Callback function
 */
export async function addLocalNotificationListener(callback) {
  try {
    await LocalNotifications.addListener('localNotificationReceived', (notification) => {
      callback(notification);
    });
  } catch (error) {
    console.error('Add local notification listener error:', error);
  }
}

/**
 * Add listener for local notification action performed
 * @param {Function} callback - Callback function
 */
export async function addLocalActionListener(callback) {
  try {
    await LocalNotifications.addListener('localNotificationActionPerformed', (action) => {
      callback(action);
    });
  } catch (error) {
    console.error('Add local action listener error:', error);
  }
}

export default {
  requestPermission,
  checkPermission,
  register,
  unregister,
  addNotificationListener,
  addActionListener,
  scheduleLocalNotification,
  cancelLocalNotification,
  getPendingNotifications,
  addLocalNotificationListener,
  addLocalActionListener
};
