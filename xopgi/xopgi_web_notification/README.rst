xopgi_web_notification (Web Notifications)
==========================================

What is this module?

This module provide a way to send web notifications_ to a some users. This
notifications shows like calendar reminder and allow put buttons_.


.. _notifications:

Notification
------------

    - id: notification identifier, it use to avoid show a same notification
      more than once at time.

    - title: text to show on notification title bar, html can be used.

    - body: text to show on notification box, html can be used.

    - actions: list of buttons_


.. _buttons:

Buttons
-------

    - id: external id or data base id for a ``ir.action`` instance. If is
      include is used to get corresponding action dict and update it with
      the rest of buttons_ values.

    - class: css class used to decorate button visual object.

    - title: text to show on notification title bar, html can be used.

    - Any other odoo action dict item.


How use
=======

To add a web notification call model method `notify` or `warn` passing
recipient user id, and notification values like this:

::

    notification = self.env['xopgi.web.notification']
    button1 = {
        'id': 'mail.action_mail_inbox_feeds',
        'title': 'go to inbox',
        'class': 'oe_highlight'
    }
    button2 = {
        'id': 237,  # data base id for project issue action on mercurio data base
        'title': 'My issues',
        'domain': [('user_id','=',uid)],
    }
    button3 = {
        'title': 'Reload',
        'type': 'ir.actions.client',
        'tag': 'reload'
    }
    for user in self.env.user.search([]):
        notification.notify(
            uid=user.id,
            id='notification_example',
            title="Notification Example",
            body="This an example of xopgi web notification",
            actions=[button1, button2, button3]
        )
