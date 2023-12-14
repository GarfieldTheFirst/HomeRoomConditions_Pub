from flask_wtf import FlaskForm
from wtforms import DateTimeLocalField, SubmitField, HiddenField
from wtforms.validators import DataRequired


class FilteringForm(FlaskForm):
    start_date = DateTimeLocalField('View data since: ',
                                    format='%Y-%m-%dT%H:%M',
                                    validators=[DataRequired()])
    timezone_offset = HiddenField('Timezone offset',
                                  validators=[DataRequired()])
    submit = SubmitField('Submit')
