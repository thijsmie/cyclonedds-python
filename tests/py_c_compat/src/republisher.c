/*
 * Copyright(c) 2006 to 2018 ADLINK Technology Limited and others
 *
 * This program and the accompanying materials are made available under the
 * terms of the Eclipse Public License v. 2.0 which is available at
 * http://www.eclipse.org/legal/epl-2.0, or the Eclipse Distribution License
 * v. 1.0 which is available at
 * http://www.eclipse.org/org/documents/edl-v10.php.
 *
 * SPDX-License-Identifier: EPL-2.0 OR BSD-3-Clause
 */

#include "dds/dds.h"
#include "dds/ddsi/ddsi_cdrstream.h"
#include "dds/ddsi/ddsi_serdata_default.h"
#include "py_c_compat.h"
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <string.h>

static const struct
{
    const char *name;
    const dds_topic_descriptor_t *descriptor
} descriptors[] = {
    {"tp_long", &py_c_compat_tp_long_desc}
};

// republisher topic
int main(int argc, char **argv)
{
    dds_entity_t participant;
    dds_entity_t topic;
    dds_entity_t reader;
    struct ddsi_serdata *samples[1];
    dds_sample_info_t infos[1];
    dds_return_t rc;
    dds_qos_t *qos;

    py_c_compat_replybytes msg;

    const dds_topic_descriptor_t *descriptor = NULL;

    assert(argc >= 2);

    for (int i = 0; i < sizeof(descriptors) / sizeof(descriptors[0]); ++i) {
        if (strcmp(descriptors[i].name, argv[1]) == 0) {
            descriptor = descriptors[i].descriptor;
        }
    }
    if (!descriptor) return 1;

    participant = dds_create_participant(0, NULL, NULL);
    if (participant < 0) return 1;

    topic = dds_create_topic(participant, descriptor, argv[1], NULL, NULL);
    if (topic < 0) return 1;

    reader = dds_create_reader(participant, topic, NULL, NULL);
    if (reader < 0) return 1;

    samples[0] = NULL;
    while (true) {
        rc = dds_readcdr(reader, samples, 1, infos, DDS_NOT_READ_SAMPLE_STATE | DDS_ANY_VIEW_STATE | DDS_ALIVE_INSTANCE_STATE);
        if (rc < 0) return 1;

        if (rc > 0)
        {
            struct ddsi_serdata_default* rserdata = (struct ddsi_serdata_default*) samples[0];
            dds_istream_t sampstream;
            dds_ostream_t keystream;
            dds_ostream_init(&keystream, 10 * 1024);
            dds_istream_from_serdata_default(&sampstream, rserdata);
            dds_stream_extract_key_from_data(&sampstream, &keystream, (const struct ddsi_sertype_default *) rserdata->c.type);

            msg.data._buffer = (char*) malloc(keystream.m_index);
            memcpy(msg.data._buffer, keystream.m_buffer, keystream.m_index);
            msg.data._maximum = keystream.m_index;
            msg.data._length = keystream.m_index;
        }
        else
        {
            dds_sleepfor(DDS_MSECS(20));
        }
    }

    dds_entity_t repltopic;
    dds_entity_t writer;

    repltopic = dds_create_topic(participant, &py_c_compat_replybytes_desc, "KeyBytes", NULL, NULL);
    if (repltopic < 0) return -1;

    writer = dds_create_writer(participant, repltopic, NULL, NULL);
    if (writer < 0) return -1;

    dds_write(writer, &msg);

    dds_sleepfor(DDS_MSECS(100));
    dds_delete(participant);

    return EXIT_SUCCESS;
}
