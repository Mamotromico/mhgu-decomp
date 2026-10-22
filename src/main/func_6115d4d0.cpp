struct Bucket {
    unsigned char pad[0x3328];
    unsigned char *ptr;
};

extern "C" void func_6115d4d0(Bucket *bucket, float value) {
    *(float *)(bucket->ptr + 0x46c) = value;
}