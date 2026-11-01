struct S {
    char pad[0x74];
    int *begin;
    int *end;
};

extern "C" int func_612d1230(S *s, unsigned int index) {
    int *begin = s->begin;
    int *end = s->end;
    unsigned int count = (unsigned int)(end - begin);
    return count > index ? begin[index] : 0;
}