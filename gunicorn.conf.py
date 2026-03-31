import os
bind = '0.0.0.0:' + os.environ.get('PORT', '5000')
workers = 2
timeout = 120
accesslog = '-'
errorlog = '-'
