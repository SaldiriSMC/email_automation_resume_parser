FROM public.ecr.aws/lambda/python:3.9

# copy requirements.txt to container root directory
COPY requirementsold.txt ./

# installing dependencies from the requirements under the root directory
RUN pip3 install -r ./requirementsold.txt
RUN python3 -m spacy download en_core_web_sm
#RUN python -m pip install 'spacy~=3.2.6'
#RUN pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.1.0/en_core_web_sm-3.1.0.tar.gz
#RUN python -m nltk.downloader punkt
COPY teak-trainer-429810-m8-3284cbd4561b.json ./
#COPY encorewebsm/ .
# Copy function code to container
COPY . ./
RUN pip list
# setting the CMD to your handler file_name.function_name
CMD [ "app.handler" ]
