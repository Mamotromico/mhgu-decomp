extern "C" void *func_60b80fd0(char *a, unsigned int b)
{
    struct Inner {
        unsigned int key;
        char pad[0x3c];
    };
    unsigned char *p = *(unsigned char **)(a + 0x64);
    unsigned int *count = (unsigned int *)(p + 0xe8);
    if (*count != 0) {
        unsigned int n = *(unsigned int *)(p + 0x70);
        if (n != 0) {
            unsigned int i = 0;
            Inner *it = *(Inner **)count;
            do {
                if (it->key == b)
                    return it;
                i++;
                it = (Inner *)((char *)it + 0x40);
            } while (i < n);
        }
    }
    return 0;
}