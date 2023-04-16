FROM public.ecr.aws/lambda/python:3.10

COPY ./lake_freeze_api/ ./lake_freeze_api/
COPY ./requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt
CMD ["lake_freeze_api.app.handler"]