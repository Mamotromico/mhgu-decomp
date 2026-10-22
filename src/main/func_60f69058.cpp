struct Inner_60f69058 {
    unsigned char pad[0x1bb];
    unsigned char field;
};

struct Outer_60f69058 {
    unsigned char pad[0x1428];
    Inner_60f69058* ptr;
};

extern "C" unsigned int func_60f69058(Outer_60f69058* obj) {
    return obj->ptr->field & 3u;
}