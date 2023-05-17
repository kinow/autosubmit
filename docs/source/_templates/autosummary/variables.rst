.. currentmodule:: {{ module }}

###################
Variables reference
###################

Autosubmit uses a variable substitution system to facilitate the development
of the templates. This variables can be used on the template in the form
``%VARIABLE_NAME%``.

All configuration variables non related to current_job or platform are
accessible by calling first to their parents. ex: ``%PROJECT.PROJECT_TYPE%``
or ``%DEFAULT.EXPID%``.

You can review all variables at any given time by using the :ref:`report <report>`
command, as shown in the example below.


.. code-block:: console

    $ autosubmit report $expid -all


Job variables
=============

{{ attributes }}


.. autoclass:: {{ objname }}
    :noindex:

    {% block attributes %}
    {% if attributes %}
    .. rubric:: {{ _('Attributes') }}

    .. autosummary::
    {% for item in attributes %}
       ~{{ name }}.{{ item }}
    {%- endfor %}
    {% endif %}
    {% endblock %}