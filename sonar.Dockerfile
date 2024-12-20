FROM sonarqube:10.8-enterprise
USER root
COPY deployment/Sonar-FGT-FW-TLS-Traffic-Inspection.cer /$JAVA_HOME/conf/security
RUN cd $JAVA_HOME/conf/security \
    && keytool -cacerts -storepass changeit -noprompt -trustcacerts -importcert -alias fortinet -file Sonar-FGT-FW-TLS-Traffic-Inspection.cer
USER sonarqube