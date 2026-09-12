# Lista de errores detectados por SonarQube

Actualmente existen **45** errores en el sistema, este aumento tiene sentido y se esperaba, esto es debido a que se actualizaraon los modulos y además de eso se añadieron modulos completos. La idea es que después de completar este documento iniciar con la correción de estos errores,  A continuación se mostra la lista completa de errores con los tipos que hay y donde se encuentran:

## Errores de seguridad: **1**
#### Using dependencies without locking resolved versions is security-sensitive.
**¿Dónde se encuentra?**
.github/workflows/ci.yml Linea 23
          `pip install --only-binary :all: -r backend/requirements.txt`
## Errores de mantebilidad: **44**
La mayoría de los errores de continuidad se repiten en varios archivos.
#### Document this HTTPException with status code 422/404/400/409 in the "responses" parameter.
Estos son varios errores pero son practicamente lo mismo, por lo cual, se va a tratar como si fuera uno ya que tienen practicamente la misma solución.  Salen 17 veces, estas 17 veces están repartidas en **3** archivos
1) En el archivo "backend/.../academic/adapters/inbound/api.py", aparece **4** veces en distintas lineas.
    Linea 77, en la 96, en la 129 y en la 131.
2) En el archivo "backend/.../reminders/adapters/inbound/http_controller.py", aparece **5** veces en distintas lineas.
    Linea 76, linea 88, linea 104, linea 111, linea 133
3) En el archivo "backend/.../usuario/adapters/inbound/api.py", aparece **8** veces en distintas lineas.
    Linea 103, linea 105, linea 129, linea 191, linea 213, linea 215, linea 217, linea 219

####  Return a value of type "TaskView" instead of "DataclassInstance" or update function "update_task" type hint.
Este problema aparece en "backend/app/modules/ai/adapters/outbound/in_memory_academic_gateway.py" En la linea 69.

#### Remove this commented out code.
Este problema aprace en la linea 15 del archivo "backend/app/modules/reminders/adapters/outbound/sqlalchemy_reminder_repository.py"

#### Refactor this exception test to have only one invocation possibly throwing an exception.
Este problema en  **3** archivos diferentes: 

1) Aparece **2** veces en el archivo "backend/tests/test_academic_task_domain.py" en la linea 28 y linea 32
2) Aparece **1** vez en el archvio "backend/tests/test_academic_update_task.py" en la linea 51
3) Aparece **1** vex en el archivo "backend/tests/test_ai_gemini_llm.py" en la linea 157

#### Split this composite assertion into separate assertions.
Este problema aparece en : "backend/tests/test_ai_handle_message.py"  en  la linea 76.

#### Remove this redundant "response_model" parameter; it duplicates the return type annotation.
Este problema aparece en 4 archivos, un total de **14** veces:
1) Aparece **2** veces en el archivo: "backend/.../academic/adapters/inbound/api.py" Linea 60 y linea 81.
2) Aparece en el archivo "backend/.../modules/ai/adapters/inbound/api.py" Linea 58
3) Aparece **6** veces en el archivo "backend/.../reminders/adapters/inbound/http_controller.py" Linea 71, linea 79, linea 83, linea 91, linea 106 y linea 121
4)  Aparece **5** veces en el archivo "backend/.../usuario/adapters/inbound/api.py" linea 93, linea 109, linea 134, linea 182, linea 200.

#### Add logic to this except clause or eliminate it and rethrow the exception automatically.
Este problema aparece en "backend/.../academic/application/use_cases/update_task.py" linea 46

#### Remove this redundant Exception class; it derives from another which is already caught.
Este problema aparece en el archivo "backend/.../usuario/adapters/inbound/api.py" linea 104(dos veces), linea 174

#### Use "Annotated" type hints for FastAPI dependency injection.
Este problema aparece en el archivo "backend/.../usuario/adapters/inbound/api.py" linea 136 y en la linea 184.

Estos problemas trataran de ser solucionados en los siguientes commits