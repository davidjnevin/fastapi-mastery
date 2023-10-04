import fastapi

from social.models import post

router = fastapi.APIRouter()

post_table = {}
comment_table = {}


def find_post(post_id: int):
    if post_id not in post_table:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail=f"Post with id {post_id} not found",
        )
    return post_table[post_id]


@router.post("/post", response_model=post.UserPost, status_code=201)
async def create_post(post: post.UserPostIn):
    data = post.dict()
    last_record_id = len(post_table)
    new_post = {**data, "id": last_record_id}
    post_table[last_record_id] = new_post
    return new_post


@router.get("/post", response_model=list[post.UserPost])
async def get_all_posts():
    return list(post_table.values())


@router.post("/comment", response_model=post.Comment, status_code=201)
async def create_comment(comment: post.CommentIn):
    post = find_post(comment.post_id)
    if not post:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail=f"Post with id {comment.post_id} not found",
        )
    data = comment.dict()
    last_record_id = len(comment_table)
    new_comment = {**data, "id": last_record_id}
    comment_table[last_record_id] = new_comment
    return new_comment


@router.get("/post/{post_id}/comment", response_model=list[post.Comment])
async def get_comments_on_post(post_id: int):
    post = find_post(post_id)
    if not post:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail=f"Post with id {post_id} not found",
        )
    return [
        comment
        for comment in comment_table.values()
        if comment["post_id"] == post_id
    ]


@router.get("/post/{post_id}", response_model=post.UserPostWithComments)
async def get_post_with_comments(post_id: int):
    post = find_post(post_id)
    if not post:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail=f"Post with id {post_id} not found",
        )
    return {
        "post": post,
        "comments": await get_comments_on_post(post_id),
    }
