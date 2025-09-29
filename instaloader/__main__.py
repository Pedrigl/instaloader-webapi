"""CLI removed

This module previously contained the full CLI implementation for the project.
To keep the codebase focused on the API server and library usage, the CLI has
been removed. The original implementation is intentionally not present to
reduce maintenance surface. If you require the CLI again, check the project's
Git history for the previous implementation.
"""

def main():
    raise SystemExit("The CLI was removed from this distribution. Use the API in instaloader.api instead.")
    g_post.add_argument('-V', '--no-videos', action='store_true',
                        help='Do not download videos.')
    g_post.add_argument('--no-video-thumbnails', action='store_true',
                        help='Do not download thumbnails of videos.')
    g_post.add_argument('-G', '--geotags', action='store_true',
                        help='Download geotags when available. Geotags are stored as a '
                             'text file with the location\'s name and a Google Maps link. '
                             'This requires an additional request to the Instagram '
                             'server for each picture. Requires login.')
    g_post.add_argument('-C', '--comments', action='store_true',
                        help='Download and update comments for each post. '
                             'This requires an additional request to the Instagram '
                             'server for each post, which is why it is disabled by default. Requires login.')
    g_post.add_argument('--no-captions', action='store_true',
                        help='Do not create txt files.')
    g_post.add_argument('--post-metadata-txt', action='append',
                        help='Template to write in txt file for each Post.')
    g_post.add_argument('--storyitem-metadata-txt', action='append',
                        help='Template to write in txt file for each StoryItem.')
    g_post.add_argument('--no-metadata-json', action='store_true',
                        help='Do not create a JSON file containing the metadata of each post.')
    g_post.add_argument('--metadata-json', action='store_true',
                        help=SUPPRESS)
    g_post.add_argument('--no-compress-json', action='store_true',
                        help='Do not xz compress JSON files, rather create pretty formatted JSONs.')
    g_prof.add_argument('-s', '--stories', action='store_true',
                        help='Also download stories of each profile that is downloaded. Requires login.')
    g_prof.add_argument('--stories-only', action='store_true',
                        help=SUPPRESS)
    g_prof.add_argument('--highlights', action='store_true',
                        help='Also download highlights of each profile that is downloaded. Requires login.')
    g_prof.add_argument('--tagged', action='store_true',
                        help='Also download posts where each profile is tagged.')
    g_prof.add_argument('--reels', action='store_true',
                        help='Also download Reels videos.')
    g_prof.add_argument('--igtv', action='store_true',
                        help='Also download IGTV videos.')

    g_cond = parser.add_argument_group("Which Posts to Download")

    g_cond.add_argument('-F', '--fast-update', action='store_true',
                        help='For each target, stop when encountering the first already-downloaded picture. This '
                             'flag is recommended when you use Instaloader to update your personal Instagram archive.')
    g_cond.add_argument('--latest-stamps', nargs='?', metavar='STAMPSFILE', const=get_default_stamps_filename(),
                        help='Store the timestamps of latest media scraped for each profile. This allows updating '
                             'your personal Instagram archive even if you delete the destination directories. '
                             'If STAMPSFILE is not provided, defaults to ' + get_default_stamps_filename())
    g_cond.add_argument('--post-filter', '--only-if', metavar='filter',
                        help='Expression that, if given, must evaluate to True for each post to be downloaded. Must be '
                             'a syntactically valid python expression. Variables are evaluated to '
                             'instaloader.Post attributes. Example: --post-filter=viewer_has_liked.')
    g_cond.add_argument('--storyitem-filter', metavar='filter',
                        help='Expression that, if given, must evaluate to True for each storyitem to be downloaded. '
                             'Must be a syntactically valid python expression. Variables are evaluated to '
                             'instaloader.StoryItem attributes.')

    g_cond.add_argument('-c', '--count',
                        help='Do not attempt to download more than COUNT posts. '
                             'Applies to #hashtag, %%location_id, :feed, and :saved.')

    g_login = parser.add_argument_group('Login (Download Private Profiles)',
                                        'Instaloader can login to Instagram. This allows downloading private profiles. '
                                        'To login, pass the --login option. Your session cookie (not your password!) '
                                        'will be saved to a local file to be reused next time you want Instaloader '
                                        'to login. Instead of --login, the --load-cookies option can be used to '
                                        'import a session from a browser.')
    g_login.add_argument('-l', '--login', metavar='YOUR-USERNAME',
                         help='Login name (profile name) for your Instagram account.')
    g_login.add_argument('-b', '--load-cookies', metavar='BROWSER-NAME',
                         help='Browser name to load cookies from Instagram')
    g_login.add_argument('-B', '--cookiefile', metavar='COOKIE-FILE',
                         help='Cookie file of a profile to load cookies')
    g_login.add_argument('-f', '--sessionfile',
                         help='Path for loading and storing session key file. '
                              'Defaults to ' + get_default_session_filename("<login_name>"))
    g_login.add_argument('-p', '--password', metavar='YOUR-PASSWORD',
                         help='Password for your Instagram account. Without this option, '
                              'you\'ll be prompted for your password interactively if '
                              'there is not yet a valid session file.')

    g_how = parser.add_argument_group('How to Download')
    g_how.add_argument('--dirname-pattern',
                       help='Name of directory where to store posts. {profile} is replaced by the profile name, '
                            '{target} is replaced by the target you specified, i.e. either :feed, #hashtag or the '
                            'profile name. Defaults to \'{target}\'.')
    g_how.add_argument('--filename-pattern',
                       help='Prefix of filenames for posts and stories, relative to the directory given with '
                            '--dirname-pattern. {profile} is replaced by the profile name,'
                            '{target} is replaced by the target you specified, i.e. either :feed'
                            '#hashtag or the profile name. Defaults to \'{date_utc}_UTC\'')
    g_how.add_argument('--title-pattern',
                       help='Prefix of filenames for profile pics, hashtag profile pics, and highlight covers. '
                            'Defaults to \'{date_utc}_UTC_{typename}\' if --dirname-pattern contains \'{target}\' '
                            'or \'{dirname}\', or if --dirname-pattern is not specified. Otherwise defaults to '
                            '\'{target}_{date_utc}_UTC_{typename}\'.')
    g_how.add_argument('--resume-prefix', metavar='PREFIX',
                       help='Prefix for filenames that are used to save the information to resume an interrupted '
                            'download.')
    g_how.add_argument('--sanitize-paths', action='store_true',
                       help='Sanitize paths so that the resulting file and directory names are valid on both '
                            'Windows and Unix.')
    g_how.add_argument('--no-resume', action='store_true',
                       help='Do not resume a previously-aborted download iteration, and do not save such information '
                            'when interrupted.')
    g_how.add_argument('--use-aged-resume-files', action='store_true', help=SUPPRESS)
    g_how.add_argument('--user-agent',
                       help='User Agent to use for HTTP requests. Defaults to \'{}\'.'.format(default_user_agent()))
    g_how.add_argument('-S', '--no-sleep', action='store_true', help=SUPPRESS)
    g_how.add_argument('--max-connection-attempts', metavar='N', type=int, default=3,
                       help='Maximum number of connection attempts until a request is aborted. Defaults to 3. If a '
                            'connection fails, it can be manually skipped by hitting CTRL+C. Set this to 0 to retry '
                            'infinitely.')
    g_how.add_argument('--commit-mode', action='store_true', help=SUPPRESS)
    g_how.add_argument('--request-timeout', metavar='N', type=float, default=300.0,
                       help='Seconds to wait before timing out a connection request. Defaults to 300.')
    g_how.add_argument('--abort-on', type=http_status_code_list, metavar="STATUS_CODES",
                       help='Comma-separated list of HTTP status codes that cause Instaloader to abort, bypassing all '
                            'retry logic.')
    g_how.add_argument('--no-iphone', action='store_true',
                        help='Do not attempt to download iPhone version of images and videos.')

    g_misc = parser.add_argument_group('Miscellaneous Options')
    g_misc.add_argument('-q', '--quiet', action='store_true',
                        help='Disable user interaction, i.e. do not print messages (except errors) and fail '
                             'if login credentials are needed but not given. This makes Instaloader suitable as a '
                             'cron job.')
    g_misc.add_argument('-h', '--help', action='help', help='Show this help message and exit.')
    g_misc.add_argument('--version', action='version', help='Show version number and exit.',
                        version=__version__)

    args = parser.parse_args()
    try:
        if (args.login is None and args.load_cookies is None) and (args.stories or args.stories_only):
            print("Login is required to download stories.", file=sys.stderr)
            args.stories = False
            if args.stories_only:
                raise InvalidArgumentException()

        if ':feed-all' in args.profile or ':feed-liked' in args.profile:
            raise InvalidArgumentException(":feed-all and :feed-liked were removed. Use :feed as target and "
                                           "eventually --post-filter=viewer_has_liked.")

        post_metadata_txt_pattern = '\n'.join(args.post_metadata_txt) if args.post_metadata_txt else None
        storyitem_metadata_txt_pattern = '\n'.join(args.storyitem_metadata_txt) if args.storyitem_metadata_txt else None

        if args.no_captions:
            if not (post_metadata_txt_pattern or storyitem_metadata_txt_pattern):
                post_metadata_txt_pattern = ''
                storyitem_metadata_txt_pattern = ''
            else:
                raise InvalidArgumentException("--no-captions and --post-metadata-txt or --storyitem-metadata-txt "
                                               "given; That contradicts.")

        if args.no_resume and args.resume_prefix:
            raise InvalidArgumentException("--no-resume and --resume-prefix given; That contradicts.")
        resume_prefix = (args.resume_prefix if args.resume_prefix else 'iterator') if not args.no_resume else None

        if args.no_pictures and args.fast_update:
            raise InvalidArgumentException('--no-pictures and --fast-update cannot be used together.')

        if args.login and args.load_cookies:
            raise InvalidArgumentException('--load-cookies and --login cannot be used together.')

        # Determine what to download
        download_profile_pic = not args.no_profile_pic or args.profile_pic_only
        download_posts = not (args.no_posts or args.stories_only or args.profile_pic_only)
        download_stories = args.stories or args.stories_only

        loader = Instaloader(sleep=not args.no_sleep, quiet=args.quiet, user_agent=args.user_agent,
                             dirname_pattern=args.dirname_pattern, filename_pattern=args.filename_pattern,
                             download_pictures=not args.no_pictures,
                             download_videos=not args.no_videos, download_video_thumbnails=not args.no_video_thumbnails,
                             download_geotags=args.geotags,
                             download_comments=args.comments, save_metadata=not args.no_metadata_json,
                             compress_json=not args.no_compress_json,
                             post_metadata_txt_pattern=post_metadata_txt_pattern,
                             storyitem_metadata_txt_pattern=storyitem_metadata_txt_pattern,
                             max_connection_attempts=args.max_connection_attempts,
                             request_timeout=args.request_timeout,
                             resume_prefix=resume_prefix,
                             check_resume_bbd=not args.use_aged_resume_files,
                             slide=args.slide,
                             fatal_status_codes=args.abort_on,
                             iphone_support=not args.no_iphone,
                             title_pattern=args.title_pattern,
                             sanitize_paths=args.sanitize_paths)
        exit_code = _main(loader,
                          args.profile,
                          username=args.login.lower() if args.login is not None else None,
                          password=args.password,
                          sessionfile=args.sessionfile,
                          download_profile_pic=download_profile_pic,
                          download_posts=download_posts,
                          download_stories=download_stories,
                          download_highlights=args.highlights,
                          download_tagged=args.tagged,
                          download_reels=args.reels,
                          download_igtv=args.igtv,
                          fast_update=args.fast_update,
                          latest_stamps_file=args.latest_stamps,
                          max_count=int(args.count) if args.count is not None else None,
                          post_filter_str=args.post_filter,
                          storyitem_filter_str=args.storyitem_filter,
                          browser=args.load_cookies,
                          cookiefile=args.cookiefile)
        loader.close()
        if loader.has_stored_errors:
            exit_code = ExitCode.NON_FATAL_ERROR
    except InvalidArgumentException as err:
        print(err, file=sys.stderr)
        exit_code = ExitCode.INIT_FAILURE
    except LoginException as err:
        print(err, file=sys.stderr)
        exit_code = ExitCode.LOGIN_FAILURE
    except InstaloaderException as err:
        print("Fatal error: %s" % err)
        exit_code = ExitCode.UNEXPECTED_ERROR
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
