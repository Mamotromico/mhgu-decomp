extern "C" int func_6069ddfc(char *obj, int key, unsigned short mask)
{
    unsigned int count = *(unsigned int *)(obj + 0x68);
    if (count != 0) {
        char **list = *(char ***)(obj + 0x74);
        unsigned int i = 0;
        do {
            char *node = list[i];
            if (node != 0) {
                signed char nodeKey = *(signed char *)(node + 0x4);
                if (nodeKey == key) {
                    unsigned int n = *(unsigned int *)(node + 0xc);
                    if (n != 0) {
                        char **arr = *(char ***)(node + 0x18);
                        unsigned int j = 0;
                        do {
                            char *e = arr[j];
                            if (e != 0) {
                                unsigned short v = *(unsigned short *)(e + 0x4);
                                if ((v & mask) != 0)
                                    return (int)e;
                            }
                            j++;
                        } while (j < n);
                    }
                }
            }
            i++;
        } while (i < count);
    }
    return 0;
}