struct func_60afe6b4_node {
    struct func_60afe6b4_node *field_0;
    unsigned int field_4;
    unsigned int field_8;
    unsigned int field_c;
};

extern "C" void func_60afe6b4(struct func_60afe6b4_node *out, struct func_60afe6b4_node *in)
{
    out->field_4 = 0;
    out->field_8 = in->field_c;
    out->field_0 = in;
    out->field_c = in->field_4;
}