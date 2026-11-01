extern "C" {

struct func_6009d184_data {
    unsigned char pad[0x1428];
    unsigned char *ptr;
};

void func_6009d184(func_6009d184_data *arg0, int arg1, int arg2)
{
    *(unsigned short *)(arg0->ptr + arg1 * 12 + 0x3be) += arg2;
}

}